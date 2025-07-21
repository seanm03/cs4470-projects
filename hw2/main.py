import kivy, os, random
from kivy.app import App
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, Line
from kivy.uix.screenmanager import ScreenManager, Screen
from itertools import combinations

# density-independent pixels stuff
def write_density():
    # critical that metrics is not loaded until other configuration is set to what we want (esp. window resolution)
    from kivy.metrics import Metrics
    if not Config.has_section('simulation'):
        Config.add_section('simulation')
    Config.set('simulation', 'density', str(Metrics.density))
    Config.write()
    return Metrics.dp


def config_kivy(window_width=None, window_height=None,
                simulate_device=False,
                simulate_dpi=None, simulate_density=None):

    target_window_width = int(window_width)
    target_window_height = int(window_height)

    config_window_width = Config.getint('graphics', 'width')
    config_window_height = Config.getint('graphics', 'height')

    if Config.has_section('simulation') and Config.has_option('simulation', 'density'):
        curr_device_density = Config.getfloat('simulation', 'density')
    else:
        curr_device_density = write_density()
        print(f"The current device density ({curr_device_density}) has been stored in the configuration")
        print(f"Now exiting, please run again to use the stored configuration.")
        exit(0)

    if simulate_device:
        # Note the following simulation strategy assumes you want to simulate the same resolution
        # window (e.g. Kivy app in windowed mode) on various devices. If you want to simulate different
        # full screen apps, then some changes are necessary.

        # For some reason, you can only override Kivy's initial DPI and Density
        # via environment variables.

        if not simulate_dpi or not simulate_density:
            raise ValueError("if simulate_device is set to True, then "
                             "simulate_dpi and simulate_density must be set!")

        print(f"Simulating device with density {simulate_density} and dpi {simulate_dpi}")

        os.environ['KIVY_DPI'] = str(simulate_dpi)
        os.environ['KIVY_METRICS_DENSITY'] = str(simulate_density)

        # This scales window size appropriately for simulation
        target_window_width = int(window_width / curr_device_density * simulate_density)
        target_window_height = int(window_height / curr_device_density * simulate_density)
    else:
        # if these are set externally, we'll ignore and use default dpi and density of device
        os.environ.pop('KIVY_DPI', None)
        os.environ.pop('KIVY_METRICS_DENSITY', None)

    if target_window_width != config_window_width or target_window_height != config_window_height:
        print(f"target_window_width: {target_window_width}, target_window_height: {target_window_height}")
        print(f"config_window_width: {config_window_width}, config_window_height: {config_window_height}")

        Config.set('graphics', 'width', str(target_window_width))
        Config.set('graphics', 'height', str(target_window_height))

    if simulate_device:
        target_window_width = window_width
        target_window_height = window_height
        print(f"Simulated resolution: {target_window_width}x{target_window_height}")
    else:
        # we can only get a reliable density if we aren't simulating (due to impact of KIVY_METRICS_DENSITY env var)
        check_density = write_density()

        if curr_device_density != check_density:
            print(f"The current device density ({check_density}) doesn't match the stored "
                  f"configuration ({curr_device_density}).")
            print(f"Therefore, updating the config to use the correct density.")
            print(f"Now exiting, please run again to use the stored configuration.")
            exit(0)

    return target_window_width, target_window_height

do_simulate = False
scr_w, scr_h = config_kivy(window_width = 800, window_height = 600,
                           simulate_device = do_simulate, simulate_dpi = 100, simulate_density = 1.0)

# NASA TLX Factors List
factors = ['Mental Demand', 'Physical Demand', 'Temporal Demand',
           'Performance', 'Effort', 'Frustration']

# methods involving factors list
def choose_two(lst):
    return list(combinations(lst, 2))

def shuffle(list, inner_shuffle = False):
    copied_list = list.copy()
    random.shuffle(copied_list)

    if inner_shuffle:
        copied_list = [tuple(random.sample(item, len(item)))
                       if isinstance(item, (tuple, list)) else item
                       for item in copied_list]

    return copied_list

def shuffle_factor_pairs(factors):
    factor_pairs = choose_two(factors)
    shuffled_factor_pairs = shuffle(factor_pairs, True)
    return shuffled_factor_pairs

# custom scale
class CustomScale(Widget):
    score = NumericProperty(0)
    visited = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos = self.update_canvas, size = self.update_canvas)
        self.bind(score = self.update_canvas)
        self.bind(visited = self.update_canvas)
        self.selected = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.selected = True
            self.update_score(touch.x)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.selected:
            self.update_score(touch.x)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.selected:
            self.selected = False
            self.visited = True
            return True
        return super().on_touch_up(touch)

    def update_score(self, x):
        self.score = int((x - self.x) / self.width * 100)
        self.score = max(0, min(100, self.score))
        self.update_canvas()
    
    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            # main line through the scale
            Color(1, 1, 1)
            Line(points = [self.x, self.center_y, self.right, self.center_y], width = 1)

            # drawing ticks
            for i in range(0, 101, 5):
                x = self.x + i / 100 * self.width
                if i == 50:
                    Line(points = [x, self.center_y - 10, x, self.center_y + 10], width = 1.5)
                else:
                    Line(points = [x, self.center_y - 5, x, self.center_y + 5], width = 1)

            # score bar in blue
            Color(0, 0, 1, 0.5)
            Rectangle(pos = (self.x, self.center_y - 2.5), size = (self.score / 100 * self.width, 5))

# classes for the screens
class PairwiseScreenLayout(Screen):
    answer_1 = ObjectProperty(None)
    answer_2 = ObjectProperty(None)
    current_question = -1
    factor_answer_amt = {}
    question_order = []
    def on_enter(self):
        if not hasattr(self.manager, 'comparisons'):
            self.manager.comparisons = shuffle_factor_pairs(factors)
        if self.current_question >= 14:
            self.update_previous_screen()
        else:
            self.update_screen()

    def update_screen(self):
        button_a = self.ids['answer_1']
        button_b = self.ids['answer_2']
        button_a.state = 'normal'
        button_b.state = 'normal'

        self.ids['next-screen'].disabled = True
        if self.current_question < 0:
            self.ids['previous-screen'].disabled = True
        else:
            self.ids['previous-screen'].disabled = False

        pair = self.manager.comparisons.pop()

        while pair in self.question_order or (pair[1], pair[0]) in self.question_order:
            pair = self.manager.comparisons.pop()

        self.ids.answer_1.text = pair[0]
        self.ids.answer_2.text = pair[1]
        self.current_question += 1
        self.question_order.append((pair[0], pair[1]))
    
    def update_previous_screen(self):
        button_a = self.ids['answer_1']
        button_b = self.ids['answer_2']
        button_a.state = 'normal'
        button_b.state = 'normal'
        self.ids['next-screen'].disabled = True

        if self.current_question <= 0:
            self.ids['previous-screen'].disabled = True
        else:
            self.ids['previous-screen'].disabled = False

        pair = self.question_order[self.current_question]
        self.ids.answer_1.text = pair[0]
        self.ids.answer_2.text = pair[1]
    
    def change_state(self, idA, idB):
        button_a = self.ids[idA]
        button_b = self.ids[idB]
        num_a = self.factor_answer_amt.setdefault(button_a.text, 0)
        num_b = self.factor_answer_amt.setdefault(button_b.text, 0)
        self.ids['next-screen'].disabled = False

        if button_a.state == 'down':
            button_b.state = 'normal'
            self.ids['next-screen'].disabled = False
            self.factor_answer_amt.update({button_a.text : (num_a + 1)})
            self.factor_answer_amt.update({button_b.text : 0}) if num_b <= 0 else self.factor_answer_amt.update({button_b.text : (num_b - 1)})
        elif button_a.state == 'normal' and button_b.state == 'normal':
            self.ids['next-screen'].disabled = True
            self.factor_answer_amt.update({button_a.text : 0}) if num_a <= 0 else self.factor_answer_amt.update({button_a.text : (num_a - 1)})
        else:
            button_b.state = 'down'
            self.ids['next-screen'].disabled = False
            self.factor_answer_amt.update({button_b.text : (num_b + 1)})
            self.factor_answer_amt.update({button_a.text : 0}) if num_a <= 0 else self.factor_answer_amt.update({button_a.text : (num_a - 1)})

    # next pair or transitions to the rating scale
    def press_next_pair(self):
        button_a = self.ids['answer_1']
        button_b = self.ids['answer_2']

        if (button_a.state == 'down' or button_b.state == 'down'):
            if len(self.question_order) >= 15:
                self.manager.current = 'ratings'
            else:
                if self.current_question < (len(self.question_order) - 1):
                    self.current_question += 1
                    self.update_previous_screen()
                else:
                    self.update_screen()
        else:
            # basically do nothing until a button has been pressed
            print("Press a button.")
    
    def press_previous_pair(self):
        if (self.current_question > 0):
            previous_question = self.question_order[self.current_question - 1]

            # decrease both factors in the dictionary
            self.factor_answer_amt.update({previous_question[0] : (self.factor_answer_amt.get(previous_question[0]) - 1)})
            self.factor_answer_amt.update({previous_question[1] : (self.factor_answer_amt.get(previous_question[1]) - 1)})

            self.current_question -= 1
            self.update_previous_screen()

class RatingsScaleLayout(Screen):
    tot_scales = 6
    visited_ct = NumericProperty(0)

    scale_answers = {}
    def on_pre_enter(self):
        self.ids['next-screen2'].disabled = True
        self.update_scales()
    
    def update_scales(self):
        for factor in factors:
            scale = CustomScale()
            self.ids[f"scale_{factor.lower().replace(' ', '_')}"].add_widget(scale)
    
    def update_visited_ct(self, widget, value):
        if value:
            self.visited_ct += 1

        if self.visited_ct == self.tot_scales:
            self.ids['next-screen2'].disabled = False

    def press_next_screen(self):
        # save scores
        is_visited = True
        for factor in factors:
            factor_ids = self.ids[f"scale_{factor.lower().replace(' ', '_')}"]
            score_to_save = factor_ids.score
            self.scale_answers.update({factor : score_to_save})

            if factor_ids.visited == False:
                is_visited = False
        if is_visited == False:
            print("Enter in a value for all scales.")
        else:
            self.manager.current = 'results'

class ResultsScreenLayout(Screen):
    def on_enter(self, *args):
        factor_answer_amt = PairwiseScreenLayout.factor_answer_amt
        scale_answers = RatingsScaleLayout.scale_answers

        total = 0
        for i in range(len(factors)):
            self.ids[f'factor_{i}'].text = factors[i]
            self.ids[f'rating_{i}'].text = str(scale_answers.get(factors[i]))
            self.ids[f'tally_{i}'].text = str(factor_answer_amt.get(factors[i]))
            self.ids[f'weight_{i}'].text = str(round(float(factor_answer_amt.get(factors[i]) / 15), 1))

            total += float((float(factor_answer_amt.get(factors[i]) / 15) * scale_answers.get(factors[i])))
        self.ids.total.text = ('Total score: ' + str(round(total, 2)))

# MainApp Class and running the UI
class MainApp(App):
    def build(self):
        Window.clearcolor = ((27/255), (27/255), (27/255), 1)
        self.title = 'NASA TLX Form'
        sm = ScreenManager()
        sm.add_widget(PairwiseScreenLayout(name = 'comparisons'))
        sm.add_widget(RatingsScaleLayout(name = 'ratings'))
        sm.add_widget(ResultsScreenLayout(name = 'results'))
        return sm

if __name__ == '__main__':
    MainApp().run()