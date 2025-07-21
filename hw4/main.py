import math, os
from pathlib import Path
from helper_functions import config_kivy
from kivy_text_metrics import TextMetrics
from kivy.app import App
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.metrics import Metrics
from kivy.uix.anchorlayout import AnchorLayout
from kivy.factory import Factory
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Line, Rectangle, Ellipse, InstructionGroup
from kivy.uix.relativelayout import RelativeLayout
from kivy.gesture import Gesture, GestureDatabase
from my_gestures import up_arrow, down_arrow, right_arrow, left_arrow, line, cross, circle

# fonts
fonts = {
	'OpenDyslexic': {"regular": "./Fonts/OpenDyslexic-Regular.ttf"},  # 0
	'FreeSerif': {"regular": "./Fonts/FreeSerif.otf"},  # 1
	'APHont': {"regular": "./Fonts/APHont-Regular_q15c.ttf"},  # 2
	'AnonymousPro': {"regular": "./Fonts/Anonymous Pro.ttf"},  # 3
	'Times': {"regular": "./Fonts/Times New Roman.ttf"},  # 4
	'Tahoma': {"regular": "./Fonts/tahoma.ttf"},  # 5
	'Helvetica': {"regular": "./Fonts/Helvetica.ttf"},  # 6
	'GaramondPro': {"regular": "./Fonts/AGaramondPro-Regular.otf"},  # 7
}

# gestures
def simple_gesture(name, point_list):
	g = Gesture()
	g.add_stroke(point_list)
	g.normalize()
	g.name = name
	return g

# density pixel thing
do_simulate = False
scr_w, scr_h = config_kivy(window_width = 1200, window_height = 600,
												simulate_device = do_simulate, simulate_dpi = 100,
												simulate_density = 1.0)

# text sizing
class ShrinkWrapLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.update_glyph_overlay,
                  pos=self.update_glyph_overlay,
                  texture=self.update_glyph_overlay,
                  font_size=self.update_glyph_overlay)

        self.kv_posted = False

    def on_kv_post(self, base_widget):
        self.kv_posted = True

    def update_glyph_overlay(self, *args):
        if not self.kv_posted: return
        if self.texture is None: return

        colors = [(1, 0, 0, 0.3), (0, 1, 0, 0.3)]  # Alternate between red and green

        # print(f"font_name: {self.font_name} font_size: {self.font_size}")

        metrics = TextMetrics(self.font_name, self.font_size)

        glyph_attribs, ascender, descender = metrics.get_text_extents(self.text, self.texture.size)

        # Calculate the label's starting position for text drawing
        # This should define the baseline
        x_offset = self.center_x - (self.texture.width / 2)
        y_offset = self.center_y + (self.texture.height / 2) - ascender

        self.canvas.after.clear()
        with self.canvas.after:
            # draw the boxes around the glyphs of the string
            for i, rect in enumerate(glyph_attribs):
                rect_x, rect_y, rect_w, rect_h, glyph_ascent, glyph_descent, x_advance = rect
                Color(*colors[i % 2])  # Alternate colors
                Rectangle(pos=(x_offset + rect_x, y_offset - glyph_descent), size=(rect_w, rect_h))

# custom classes for this assignment
class PopupFile(Popup):
	def __init__(self, main_app, **kwargs):
		super(PopupFile, self).__init__(**kwargs)
		self.main_app = main_app

	def selected(self, filename):
		# resets vars
		self.main_app.wordlist = []
		self.main_app.curr_word = ''
		self.main_app.curr_idx = 0
		self.main_app.word_label.text = ''
		try:
			with open(filename[0]) as f:
				contents = f.read()
				# print(contents)
				self.main_app.load_wordlst(contents)
			self.dismiss()
			self.main_app.ids['pause'].disabled = False
			self.main_app.create_dropdown()
		except Exception as e:
			print(f"Error: {e}")

class PauseButton(Button):
	def __init__(self, **kwargs):
		super(PauseButton, self).__init__(**kwargs)

class MainScreen(Screen):
	curr_word = ''
	wordlst = []
	curr_idx = 0
	is_running = False
	wpm = 150
	curr_font_size = 24
	curr_font_type = 'Helvetica'
	is_in_bounds = True

	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)

		# pause/play button
		self.ids['pause'].background_normal = 'imgs/play_icon.png'
		self.ids['pause'].background_disabled_normal = 'imgs/play_icon_disabled.png'

		self.dropdown = DropDown()
		self.create_dropdown()

		# word label instantiation
		self.pos_label = RelativeLayout(size = self.size, size_hint = (None, None))

		fpath = os.path.abspath(__file__)
		fpath = fpath[:fpath.rfind(os.sep)] + os.sep
		init_font = fonts[self.curr_font_type]['regular']
		self.word_label = ShrinkWrapLabel(text = 'dummy text', font_name = f'{fpath}{init_font}',
									size_hint = (None, None), font_size = int(24 * Metrics.dp),
									markup = True)

		self.pos_label.add_widget(self.word_label)
		self.add_widget(self.pos_label)

		# print(self.word_label.font_name)
		# print(os.path.exists(self.word_label.font_name))
		self.draw_baseline_focus_lines()
		self.word_label.text = ''

		# keyboard instantiation
		self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
		self._keyboard.bind(on_key_down = self._on_keyboard_down)

		# gesture instantiation
		self.gdb = GestureDatabase()
		self.gdb.add_gesture(right_arrow)
		self.gdb.add_gesture(left_arrow)
		self.gdb.add_gesture(up_arrow)
		self.gdb.add_gesture(down_arrow)
		self.gdb.add_gesture(cross) # increase font size
		self.gdb.add_gesture(line) # decrease font size
		self.gdb.add_gesture(circle) # pause/play

		self.x_min, self.x_max = 20 * Metrics.dp, 1180 * Metrics.dp
		self.y_min, self.y_max = 130 * Metrics.dp, 490 * Metrics.dp

		self.gesture_instrct = None

	# canvas drawing
	def draw_baseline_focus_lines(self):
		self.word_label.texture_update()
		if self.word_label.texture is None: return False
		metrics = TextMetrics(self.word_label.font_name, self.word_label.font_size)
		glyph_attribs, ascender, descender = metrics.get_text_extents(self.word_label.text,
																self.word_label.texture.size)
		
		self.line_group = InstructionGroup()

		Color(1, 1, 1, 1)

		x_ofst = 600 * Metrics.dp
		y_ofst = 300 * Metrics.dp + (self.word_label.texture.height / 2) - ascender


		# bottom part of baseline
		bb_l = Line(points = [(x_ofst * 0.5), (y_ofst - ascender - (self.curr_font_size / 2)),
				(x_ofst * 1.5), (y_ofst - ascender - (self.curr_font_size / 2))],
				width = 1.2)

		# top part of baseline
		tb_l = Line(points = [(x_ofst * 0.5), (y_ofst + (ascender * 2)),
				(x_ofst * 1.5), (y_ofst + (ascender * 2))],
				width = 1.2)
		
		# Color(1, 1, 1, 1)
		# bottom part of focus
		bf_l = Line(points = [x_ofst, (y_ofst - ascender - (self.curr_font_size / 2)),
				x_ofst, (y_ofst - ascender)], width = 1)
		
		# top part of focus
		tf_l = Line(points = [x_ofst, (y_ofst + (ascender * 2)),
				x_ofst, (y_ofst + ((ascender * 2) - (self.curr_font_size / 2)))], width = 1)
		
		self.line_group.add(bb_l)
		self.line_group.add(tb_l)
		self.line_group.add(bf_l)
		self.line_group.add(tf_l)
		self.canvas.add(self.line_group)

	def clear_lines(self):
		self.canvas.remove(self.line_group)

	# dropdown/popup for files
	def create_dropdown(self):
		self.dropdown.clear_widgets()
		for item in ["WPM", "Font", "Font Size"]:
			# popup = Popup(auto_dismiss = True, size_hint = (0.8, 0.8),
			# 	pos_hint = {'center_x': 0.5, 'center_y': 0.5})
			
			if item == "WPM":
				spinner_wpm = Spinner(text = '150 wpm', values = ('100 wpm', '150 wpm', '200 wpm', '250 wpm', '300 wpm',
												 '400 wpm', '600 wpm'), size_hint = (None, None),
												 height = 44 * Metrics.dp)
				spinner_wpm.bind(text = lambda instance, value: self.change_wpm(value))
				self.dropdown.add_widget(spinner_wpm)
			elif item == "Font":
				spinner_font = Spinner(text = 'Helvetica', values = ('OpenDyslexic', 'FreeSerif', 'APHont',
												  'AnonymousPro', 'Times', 'Tahoma',
												  'Helvetica', 'GaramondPro'),
												size_hint = (None, None), height = 44 * Metrics.dp)
				spinner_font.bind(text = lambda instance, value: self.change_font_type(value))
				self.dropdown.add_widget(spinner_font)
			elif item == "Font Size":
				spinner_font_size = Spinner(text = '24', values = ('24', '28', '32', '36', '40', '44', '48'),
								size_hint = (None, None), height = 44 * Metrics.dp)
				spinner_font_size.bind(text = lambda instance, value: self.change_font_size(value))
				self.dropdown.add_widget(spinner_font_size)
		# main button instantiation
		anchor = AnchorLayout(anchor_x = 'right', anchor_y = 'top')
		main_button = Button(background_normal = 'imgs/gear_icon_normal.png', background_down = 'imgs/gear_icon_down.png',
					   size_hint = (None, None))
		main_button.bind(on_release = self.dropdown.open)

		anchor.add_widget(main_button)
		self.add_widget(anchor)

	def show_popup(self, instance):
		popup_file = PopupFile(main_app = self)
		popup_file.open()
	
	# word manipulation
	def load_wordlst(self, contents):
		self.wordlst = contents.split()
		self.curr_word = self.wordlst[self.curr_idx]
		highlighted_letter = self.highlight_letter()
		self.center_to_highlighted_letter(highlighted_letter)

	def display_next_word(self):
		if self.is_running == False: return
		self.curr_idx = (self.curr_idx) % len(self.wordlst)
		if self.curr_idx == len(self.wordlst) - 1:
			# end of the word list
			self.curr_word = self.wordlst[self.curr_idx]
			self.center_to_highlighted_letter(self.highlight_letter())
			self.ids['pause'].background_normal = 'imgs/play_icon.png'
			self.stop_display()

			self.curr_word = self.wordlst[0]
			self.curr_idx = 0
			return

		self.curr_word = self.wordlst[self.curr_idx]
		#self.word_label.text = self.curr_word

		display_time = self.calc_display_time(self.curr_word)
		self.center_to_highlighted_letter(self.highlight_letter())
		Clock.schedule_once(lambda dt: self.display_next_word(), display_time)
		self.curr_idx += 1

	def highlight_letter(self):
		marked_letter_idx = 0
		if len(self.curr_word) > 6: marked_letter_idx = math.floor(len(self.curr_word) // 3)
		elif len(self.curr_word) > 2: marked_letter_idx = math.floor(len(self.curr_word) // 2)
		
		letters_before = self.curr_word[:marked_letter_idx]
		marked_letter = self.curr_word[marked_letter_idx]
		letters_after = self.curr_word[(marked_letter_idx + 1):]

		self.word_label.text = f'{letters_before}[color=ff7f7f]{marked_letter}[/color]{letters_after}'

		return marked_letter_idx
	
	def center_to_highlighted_letter(self, marked_letter_idx):
		if self.word_label.texture is None: return
		
		# print(self.word_label.font_name)
		metrics = TextMetrics(self.word_label.font_name, self.word_label.font_size)
		glyph_attribs, ascender, descender = metrics.get_text_extents(self.word_label.text,
																self.word_label.texture_size)
		if marked_letter_idx >= len(glyph_attribs): return

		adv_to_mark = sum(glyph_attribs[i][6] for i in range(marked_letter_idx + 1))
		marked_letter_spot = glyph_attribs[marked_letter_idx][6]
		after_mls = sum(attr[6] for attr in glyph_attribs)

		scale = self.pos_label.width / (after_mls - 1)
		dist_to_mark = adv_to_mark * scale * Metrics.dp
		marked_letter_width = marked_letter_spot * scale * Metrics.dp

		screen_center_x = self.width / 2
		xpos = screen_center_x - dist_to_mark - (marked_letter_width) - (self.word_label.font_size * Metrics.dp)
		self.pos_label.x = xpos

		self.pos_label.y = (self.height / 2) - (self.word_label.height / 2)

	# keyboard stuff
	def _keyboard_closed(self):
		self._keyboard.unbind(on_key_down = self._on_keyboard_down)
		self._keyboard = None

	def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
		if keycode[1] == 'spacebar': self.on_press_pauseplaybtn()
		elif keycode[1] == '-':
			if self.curr_font_size > 6:
				self.change_font_size(self.curr_font_size - 2)
		elif keycode[1] == '+' or keycode[1] == '=':
			if self.curr_font_size < 60:
				self.change_font_size(self.curr_font_size + 2)
		elif keycode[1] == 'up':
			if self.wpm < 1000:
				self.wpm = self.wpm + 30
		elif keycode[1] == 'down':
			if self.wpm > 30:
				self.wpm = self.wpm - 30
		elif keycode[1] == 'left':
			jump_back_sec = 4
			words_per_sec = float(self.wpm / 60)
			jump_back_words = int(jump_back_sec * words_per_sec)

			self.curr_idx = max(0, (self.curr_idx - jump_back_words))
		elif keycode[1] == 'right':
			jump_fwd_sec = 4
			words_per_sec = float(self.wpm / 60)
			jump_fwd_words = int(jump_fwd_sec * words_per_sec)

			self.curr_idx = max(0, (self.curr_idx + jump_fwd_words))

		return True

	# gesture stuff
	def is_within_bounds(self, x, y):
		return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

	def on_touch_down(self, touch):
		if self.is_within_bounds(touch.x, touch.y):
			self.clear_gesture()
			self.gesture_instrct = InstructionGroup()
			self.gesture_instrct.add(Color(1, 0, 0, 1))
			d = 30.0
			e = Ellipse(pos = (touch.x - d / 2, touch.y - d / 2), size = (d, d))
			touch.ud['line'] = Line(points = (touch.x, touch.y))
			self.gesture_instrct.add(touch.ud['line'])
			self.gesture_instrct.add(e)
			self.canvas.add(self.gesture_instrct)
			self.is_in_bounds = True
			return True
		else: self.is_in_bounds = False
		return super(MainScreen, self).on_touch_down(touch)

	def on_touch_up(self, touch):
		if not self.is_within_bounds(touch.x, touch.y) or not self.is_in_bounds:
			self.clear_gesture()
			return super(MainScreen, self).on_touch_up(touch)

		g = simple_gesture('', list(zip(touch.ud['line'].points[::2],
								  touch.ud['line'].points[1::2])))

		g2 = self.gdb.find(g, minscore = 0.5)
		if g2:
			if g2[1] == up_arrow:
				if self.wpm < 1000:
					self.wpm = self.wpm + 60
			if g2[1] == down_arrow:
				if self.wpm > 30:
					self.wpm = self.wpm - 60
			if g2[1] == left_arrow:
				jump_back_sec = 4
				words_per_sec = float(self.wpm / 60)
				jump_back_words = int(jump_back_sec * words_per_sec)

				self.curr_idx = max(0, (self.curr_idx - jump_back_words))
			if g2[1] == right_arrow:
				jump_fwd_sec = 4
				words_per_sec = float(self.wpm / 60)
				jump_fwd_words = int(jump_fwd_sec * words_per_sec)

				self.curr_idx = max(0, (self.curr_idx + jump_fwd_words))
			if g2[1] == cross:
				if self.curr_font_size < 60:
					self.change_font_size(self.curr_font_size + 6)
			if g2[1] == line:
				if self.curr_font_size > 6:
					self.change_font_size(self.curr_font_size - 6)
			if g2[1] == circle:
				self.on_press_pauseplaybtn()
		self.clear_gesture()
		return super(MainScreen, self).on_touch_up(touch)

	def on_touch_move(self, touch):
		if 'line' in touch.ud:
			if self.is_within_bounds(touch.x, touch.y) or self.is_in_bounds:
				touch.ud['line'].points += [touch.x, touch.y]
			return True
		return super(MainScreen, self).on_touch_move(touch)

	def clear_gesture(self):
		if self.gesture_instrct:
			self.canvas.remove(self.gesture_instrct)
			self.gesture_instrct = None

	# display/wpm/font
	def start_display(self):
		if self.curr_idx != len(self.wordlst) - 1:
			Clock.unschedule(self.display_next_word)
			self.display_next_word()
		else:
			self.stop_display()
	
	def stop_display(self):
		self.is_running = False
		Clock.unschedule(self.display_next_word)
	
	def change_wpm(self, wpm):
		self.wpm = int(wpm.split()[0])
	
	def calc_display_time(self, word):
		sec_per_word = float(60 / self.wpm)
		word_itvl = round(float((len(word) / 2.5) * sec_per_word), 4)
		print(f'{self.wordlst[self.curr_idx]}, {word_itvl}')
		return word_itvl

	def change_font_size(self, curr_font_size):
		self.curr_font_size = int(curr_font_size)

		self.word_label.font_size = int(self.curr_font_size * Metrics.dp)
		self.word_label.texture_update()

		if self.word_label.texture is None: return False
		else:
			self.clear_lines()
			self.draw_baseline_focus_lines()
	
	def change_font_type(self, curr_font_type):
		self.curr_font_type = curr_font_type

		fpath = os.path.abspath(__file__)
		fpath = fpath[:fpath.rfind(os.sep)] + os.sep
		sel_font = fonts[self.curr_font_type]['regular']
		fpath = f'{fpath}{sel_font}'

		if os.path.exists(fpath):
			print(fpath)
			self.word_label.font_name = fpath
		else:
			print('no path found')
			return

	# pause/play
	def on_press_pauseplaybtn(self):
		if len(self.wordlst) < 1: print('No text loaded')
		elif self.is_running == True:
			self.is_running = False
			self.ids['pause'].background_normal = 'imgs/play_icon.png'
			self.stop_display()
		else:
			self.is_running = True
			self.ids['pause'].background_normal = 'imgs/pause_icon.png'
			self.start_display()

class MainApp(App):

	def build(self):
		Window.clearcolor = ((27/255), (27/255), (27/255), 1)
		self.title = 'RSVP Text Reader'
		sm = ScreenManager()
		sm.add_widget(MainScreen(name = 'main'))
		return sm

if __name__ == '__main__': MainApp().run()