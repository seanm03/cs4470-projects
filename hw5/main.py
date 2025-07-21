from helper_functions import config_kivy, write_density
import json, os
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.properties import ListProperty, StringProperty
from kivy.metrics import Metrics
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.audio import SoundLoader

do_simulate = False
scr_w, scr_h = config_kivy(window_width = 800, window_height = 600,
												simulate_device = do_simulate, simulate_dpi = 100,
												simulate_density = 1.0)

filepath = os.path.join(os.path.dirname(__file__), 'levels-1.txt')

sounds = {
    'jump-1': './sounds/jump-1.wav',
    'jump-2': './sounds/jump-2.wav',
    'clone-1': './sounds/clone-1.wav',
    'clone-2': './sounds/clone-2.wav',
    'capture-1': './sounds/capture-1.wav',
    'capture-2': './sounds/capture-2.wav',
    'victory': './sounds/victory.wav'
}

# custom objects
class CircleButton(ToggleButtonBehavior, Widget):
    background_color = ListProperty([0, 0, 0, 1])
    circle_color = ListProperty([1, 1, 1, 1])
    background_normal, background_down = StringProperty(''), StringProperty('')
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._circle_draw, 0)
    
    def _circle_draw(self, dt = None):
        if self.canvas:
            self.canvas.clear()
            with self.canvas:
                Color(*self.background_color)
                self.rect = Rectangle(pos = self.pos, size = self.size)
                Color(*self.circle_color)
                self.circle = Ellipse(pos = self.pos, size = self.size)
    
    def _circle_update(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.circle_color)
            Ellipse(pos = self.pos, size = self.size)

    def on_size(self, *args): self._circle_draw()
    
    def on_pos(self, *args): self._circle_draw()

    def on_background_Color(self, *args): self._circle_draw()

    def on_circle_color(self, *args): self._circle_draw()

# screens
class StartMenu(Screen):
    sel_lvl, sel_time_mode = '', ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for button in [self.ids.board_1, self.ids.board_2, self.ids.board_3,
                       self.ids.board_4, self.ids.untimed, self.ids.timed]:
            button.bind(state = self.on_btn_state)
    
    def on_btn_state(self, instance, value):
        if value == 'down':
            if (instance.group == 'sel_board_grp'): self.sel_lvl = int(instance.custom_value)
            else: self.sel_time_mode = instance.custom_value
        else:
            if (instance.group == 'sel_board_grp'): self.sel_lvl = ''
            else: self.sel_time_mode = ''

    def press_submitbtn(self):
        if (self.sel_lvl and self.sel_time_mode):
            with open(filepath, 'r') as file: lvl_data = json.load(file)
            App.get_running_app().board_data = lvl_data[self.sel_lvl - 1]['board']
            App.get_running_app().timer_setting = self.sel_time_mode
            self.manager.current = 'main'
        else: print('Select a button first')

class MainGameScreen(Screen):
    plr1_score, plr2_score = 2, 2
    plr1_time, plr2_time = 60, 60
    fpath = os.path.abspath(__file__)[:os.path.abspath(__file__).rfind(os.sep)] + os.sep
    is_timed, timed_out = False, False
    def __init__(self, **kwargs):
        super(MainGameScreen, self).__init__(**kwargs)
        self.sel_piece, self.board_layout, self.piece_flayout = None, None, None
        self.valid_moves, self.cell_list, self.piece_list = [], [], []
        self.curr_turn = True # true for red, false for blue
        self.board_size = 7

    def on_enter(self):
        self.board_update(App.get_running_app().board_data,
                          App.get_running_app().timer_setting)
        self.draw_init_pieces()

    def board_update(self, board_data, timer_setting):
        self.clear_widgets()

        self.board_layout = GridLayout(cols = self.board_size, padding = 10 * Metrics.dp,
                            spacing = 2 * Metrics.dp, size_hint = (0.67, 0.8),
                            pos_hint = {'center_x': 0.5, 'center_y': 0.45})

        for row in board_data:
            for cell in row:
                if cell == 9:
                    btn = Button(size_hint = (1, 1), background_normal = '',
                                background_color = (1, 1, 0, 1), disabled = True)
                else:
                    btn = Button(size_hint = (1, 1), background_normal = '',
                                 background_color = (0.3, 0.3, 0.3, 1))
                self.cell_list.append(btn)
                btn.bind(on_press = self.on_cell_sel)
                self.board_layout.add_widget(btn)
        plr1_alayout = AnchorLayout(anchor_x = 'left', anchor_y = 'top',
                                    padding = 5 * Metrics.dp, size_hint = (0.3, 0.3),
                                    pos_hint = {'center_x': 0.2, 'center_y': 0.9})
        self.score1_label = Label(color = (1, 0, 0, 1), font_size = 20 * Metrics.dp,
                                  text = 'P1 Score: 1')
        plr1_alayout.add_widget(self.score1_label)
        self.add_widget(plr1_alayout)

        plr2_alayout = AnchorLayout(anchor_x = 'right', anchor_y = 'top',
                                    padding = 5 * Metrics.dp, size_hint = (0.3, 0.3),
                                    pos_hint = {'center_x': 0.8, 'center_y': 0.9})
        self.score2_label = Label(color = ((88/255), (105/255), (232/255), 1),
                                  font_size = 20 * Metrics.dp, text = 'P2 Score: 1')
        plr2_alayout.add_widget(self.score2_label)
        self.add_widget(plr2_alayout)

        if timer_setting == '2':
            timer1 = AnchorLayout(anchor_x = 'center', anchor_y = 'top', padding = 5 * Metrics.dp,
                                 size_hint = (0.2, 0.2),
                                 pos_hint = {'center_x': 0.35, 'center_y': 0.9})
            self.timer1_label = Label(font_size = 20 * Metrics.dp, color = (1, 0, 0, 1),
                                      text = 'Timer: 01:00')
            timer1.add_widget(self.timer1_label)
            self.add_widget(timer1)

            timer2 = AnchorLayout(anchor_x = 'center', anchor_y = 'top', padding = 5 * Metrics.dp,
                                 size_hint = (0.2, 0.2),
                                 pos_hint = {'center_x': 0.65, 'center_y': 0.9})
            self.timer2_label = Label(color = ((88/255), (105/255), (232/255), 1),
                                  font_size = 20 * Metrics.dp, text = 'Timer: 01:00')
            timer2.add_widget(self.timer2_label)
            self.add_widget(timer2)

            self.timer_start()
        self.add_widget(self.board_layout)
    
    def timer_start(self): self.timer_event = Clock.schedule_interval(self.timer_update, 1)

    def timer_update(self, dt = None):
        if self.curr_turn:
            self.plr1_time -= 1
            self.timer1_label.text = f'Timer: 00:{self.plr1_time}'
            self.timer1_label.color = (1, 0, 0, 1)
            self.timer2_label.color = ((88/255), (105/255), (232/255), 0.5)
        else:
            self.plr2_time -= 1
            self.timer2_label.text = f'Timer: 00:{self.plr2_time}'
            self.timer2_label.color = ((88/255), (105/255), (232/255), 1)
            self.timer1_label.color = (1, 0, 0, 0.5)

        if self.plr1_time <= 0 or self.plr2_score <= 0: self.manager.current = 'end'

    def draw_init_pieces(self, *args):
        self.plr1_score, self.plr2_score = 2, 2
        self.plr1_time, self.plr2_time = 60, 60
        self.curr_turn = True
        self.piece_flayout = FloatLayout(size_hint = (0.65, 0.78),
                                   pos_hint = {'center_x': 0.5, 'center_y': 0.45})
        init_pos = [
            (0, 0, 'plr_1'), (6, 6, 'plr_1'),
            (0, 6, 'plr_2'), (6, 0, 'plr_2')
        ]

        for x, y, group in init_pos:
            piece = CircleButton(background_color = (0, 0, 0, 0),
                                 size = (75 * Metrics.dp, 75 * Metrics.dp),
                                 size_hint = (None, None),
                                 pos_hint = {'center_x': (x + 0.5) / self.board_size,
                                             'center_y': 1 - (y + 0.5) / self.board_size},
                                 circle_color = (1, 0, 0, 1) if group == 'plr_1'
                                 else (0, 0, 1, 1), group = group)
            self.piece_list.append(piece)
            self.piece_flayout.add_widget(piece)
            piece.bind(on_press = self.on_piece_sel)
        self.add_widget(self.piece_flayout)
    
    def on_piece_sel(self, instance):
        cell = self.get_cell_at_piece(instance)
        self.on_cell_sel(cell)

    def on_cell_sel(self, instance):
        if self.sel_piece is None:
            piece = self.get_piece_at_cell(instance)
            if piece and piece.group == ('plr_1' if self.curr_turn else 'plr_2'):
                self.sel_piece = piece
                self.show_valid_moves(instance)
        else:
            if instance in self.valid_moves: self.move_piece(self.sel_piece, instance)
            self.clear_highlight()
            self.sel_piece = None
    
    def show_valid_moves(self, p):
        x, y = self.get_cell_coords(p)
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                x_new, y_new = x + dx, y + dy
                if 0 <= x_new < self.board_size and 0 <= y_new < self.board_size:
                    cell = self.cell_list[(y_new * self.board_size + x_new)]
                    if (cell.background_color != [1, 1, 0, 1] and
                        self.get_piece_at_cell(cell) is None):
                        cell.background_color = [0.9, 0.9, 0.9, 1]
                        self.valid_moves.append(cell)
    
    def get_piece_at_cell(self, cell):
        cell_pos = self.get_cell_coords(cell)
        for piece in self.piece_list:
            piece_pos = self.get_piece_coords(piece)
            if piece_pos == cell_pos: return piece
        return None

    def get_cell_at_piece(self, piece):
        piece_pos = self.get_piece_coords(piece)
        for cell in self.cell_list:
            cell_pos = self.get_cell_coords(cell)
            if cell_pos == piece_pos: return cell
        return None
    
    def get_piece_coords(self, piece):
        return int(piece.pos_hint['center_x'] * self.board_size - 0.5), int((1 - piece.pos_hint['center_y']) * self.board_size - 0.5)

    def get_cell_coords(self, cell):
        if cell in self.cell_list:
            idx = self.cell_list.index(cell)
            return idx % self.board_layout.cols, idx // self.board_layout.cols
        return None

    def move_piece(self, piece, cell):
        x_old, y_old = self.get_piece_coords(piece)
        x_new, y_new = self.get_cell_coords(cell)

        new_pos_hint = {
            'center_x': (x_new + 0.5) / self.board_size,
            'center_y': 1 - (y_new + 0.5) / self.board_size
        }

        sound_to_play = ''

        if abs(x_old - x_new) >= 2 or abs(y_old - y_new) >= 2:
            anim = Animation(pos_hint = new_pos_hint, duration = 0.2)
            anim &= (Animation(size = (95 * Metrics.dp, 65 * Metrics.dp), duration = 0.15) +
                     Animation(size = (75 * Metrics.dp, 75 * Metrics.dp), duration = 0.15))
            anim.start(piece)
            sound_to_play = 'jump-'
        else:
            anim = Animation(pos_hint = new_pos_hint, duration = 0.2)
            anim.start(piece)
            sound_to_play = 'jump-'

        if abs(x_old - x_new) <= 1 and abs(y_old - y_new) <= 1:
            self.clone_piece(piece, x_old, y_old)
            sound_to_play = 'clone-'
        
        if self.capture_adj_piece(piece, x_new, y_new): sound_to_play = 'capture-'

        if self.curr_turn: sound_list = sounds[sound_to_play + '1']
        else: sound_list = sounds[sound_to_play + '2']
        sound = SoundLoader.load(self.fpath + sound_list)
        if sound: sound.play()
        self.curr_turn = not self.curr_turn

    def capture_adj_piece(self, piece, x, y):
        visited = set()
        stack = [(x, y)]
        is_capture = False
        while stack:
            x_curr, y_curr = stack.pop()
            if (x_curr, y_curr) in visited: continue
            visited.add((x_curr, y_curr))

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                           (-1, -1), (1, 1), (-1, 1), (1, -1)]:
                x_adj, y_adj = x_curr + dx, y_curr + dy
                if 0 <= x_adj < self.board_size and 0 <= y_adj < self.board_size:
                    cell_adj = self.cell_list[y_adj * self.board_size + x_adj]
                    piece_adj = self.get_piece_at_cell(cell_adj)
                    if piece_adj and piece_adj.group != piece.group:
                        piece_adj.circle_color = piece.circle_color
                        piece_adj.group = piece.group
                        piece_adj._circle_update()
                        is_capture = True
                        stack.append((x_adj, y_adj))
                        pos_hint_right = {'center_x': (piece_adj.pos_hint['center_x'] + 0.03),
                                          'center_y': (piece_adj.pos_hint['center_y'] - 0.005)}
                        pos_hint_left = {'center_x': (piece_adj.pos_hint['center_x'] + 0.03),
                                         'center_y': (piece_adj.pos_hint['center_y'] - 0.005)}

                        anim = (Animation(pos_hint = pos_hint_left, duration = 0.12) +
                                Animation(pos_hint = pos_hint_right, duration = 0.1) +
                                Animation(pos_hint = piece_adj.pos_hint, duration = 0.1))
                        anim.start(piece_adj)
                        if self.curr_turn: self.plr2_score -= 1
                        else: self.plr1_score -= 1
                        self.score_update()
        return is_capture

    def clone_piece(self, piece, x, y):
        new_piece = CircleButton(background_color = (0, 0, 0, 0),
                                 size = (75 * Metrics.dp, 75 * Metrics.dp),
                                 size_hint = (None, None),
                                 pos_hint = {'center_x': (x + 0.5) / self.board_size,
                                             'center_y': 1 - (y + 0.5) / self.board_size},
                                 circle_color = piece.circle_color,
                                 group = piece.group)
        self.piece_list.append(new_piece)
        self.piece_flayout.add_widget(new_piece)
        piece.bind(on_press = self.on_piece_sel)

        anim = (Animation(size = (90 * Metrics.dp, 90 * Metrics.dp), duration = 0.15) +
                Animation(size = (75 * Metrics.dp, 75 * Metrics.dp), duration = 0.15))
        anim.start(new_piece)
        self.score_update()

    def clear_highlight(self):
        for cell in self.valid_moves: cell.background_color = [0.3, 0.3, 0.3, 1]
        self.valid_moves = []

    def score_update(self):
        if self.curr_turn: self.plr1_score += 1
        else: self.plr2_score += 1
        self.score1_label.text = 'P1 Score: ' + str(self.plr1_score)
        self.score2_label.text = 'P2 Score: ' + str(self.plr2_score)

        if self.plr1_score <= 0 or self.plr2_score <= 0: self.manager.current = 'end'
        
class EndGameScreen(Screen):
    def on_pre_enter(self):
        plr1_score = self.manager.get_screen('main').plr1_score
        plr2_score = self.manager.get_screen('main').plr2_score
        fpath = self.manager.get_screen('main').fpath

        if plr1_score >= plr2_score: self.ids['winner'].text = 'Player 1 Wins.'
        else: self.ids['winner'].text = 'Player 2 Wins.'

        sound_list = sounds['victory']
        sound = SoundLoader.load(fpath + sound_list)
        if sound: sound.play()
    
    def press_btn(self): self.manager.current = 'start'

class MainApp(App):
    def build(self):
        Window.clearcolor = ((27/255), (27/255), (27/255), 1)
        self.title = 'Ataxx'

        sm = ScreenManager()
        sm.add_widget(StartMenu(name = 'start'))
        sm.add_widget(MainGameScreen(name = 'main'))
        sm.add_widget(EndGameScreen(name = 'end'))
        return sm

if __name__ == '__main__': MainApp().run()