import kivy, os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, AliasProperty, BooleanProperty
# from kivy.lang import Builder -- not used
from kivy.core.window import Window
from kivy_config_helper import config_kivy
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.core.image import Image as CoreImage
from kivy.graphics import Rectangle, Color

# density-independent pixels stuff
do_simulate = False
scr_w, scr_h = config_kivy(window_width = 400, window_height = 500,
                           simulate_device = do_simulate, simulate_dpi = 100, simulate_density = 1.0)

# alt checkbox stuff
IMG_FOLDER = "./images/"
IMG_CHECKBOX_ON = os.path.join(IMG_FOLDER, "checkbox_on.png")
IMG_CHECKBOX_OFF = os.path.join(IMG_FOLDER, "checkbox_off.png")

# custom text input for name
class InputName(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False

    def insert_text(self, substring, from_undo = False):
        # filters input to just 
        filtered_chars = ''.join([char for char in substring if char.isalpha()
                                  or (char == ' ' and ' ' not in self.text)])
        return super().insert_text(filtered_chars, from_undo)

# class for alternate check-box ripped from alt_checkbox.py
class AltCheckBox(ToggleButtonBehavior, Widget):
    keep_ratio = BooleanProperty(True)  # Option to keep aspect ratio, defaults to True

    def __init__(self, **kwargs):
        super(AltCheckBox, self).__init__(**kwargs)
        self.bind(size=self.update_texture, pos=self.update_texture, state=self.update_texture)
        self.texture = None
        self.update_texture()

    def get_widget_screen_size(self):
        x1, y1 = self.to_window(0, 0)
        x2, y2 = self.to_window(self.width, self.height)
        return abs(x2 - x1), abs(y2 - y1)

    def update_texture(self, *args):
        # Choose the correct image based on the toggle state
        img_file = IMG_CHECKBOX_ON if self.state == 'down' else IMG_CHECKBOX_OFF
        img = CoreImage(img_file).texture

        # Get the screen size of the widget
        widget_width, widget_height = self.get_widget_screen_size()

        # Get the image aspect ratio
        img_width, img_height = img.size
        img_aspect = img_width / img_height

        # Initialize offset values to 0 (no offset by default)
        offset_x = 0
        offset_y = 0

        # Calculate the best fit size while maintaining aspect ratio
        if self.keep_ratio:
            widget_aspect = widget_width / widget_height

            if img_aspect > widget_aspect:
                # The image is wider than the widget area; scale by width
                scaled_width = widget_width
                scaled_height = widget_width / img_aspect
                offset_y = (widget_height - scaled_height) / 2  # Center vertically
            else:
                # The image is taller than the widget area; scale by height
                scaled_height = widget_height
                scaled_width = widget_height * img_aspect
                offset_x = (widget_width - scaled_width) / 2  # Center horizontally
        else:
            # If keep_ratio is False, just use the full widget size
            scaled_width, scaled_height = widget_width, widget_height

        # Apply texture to the widget with the calculated size and centered position
        self.texture = img
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1, 1)  # White color for the background
            Rectangle(texture=self.texture, pos=[self.pos[0] + offset_x, self.pos[1] + offset_y], size=[scaled_width, scaled_height])

    def _get_active(self):
        return self.state == 'down'

    def _set_active(self, value):
        self.state = 'down' if value else 'normal'

    active = AliasProperty(_get_active, _set_active, bind=('state',), cache=True)

# custom text input for phone number
class InputPhone(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.input_filter = 'int'
        self.bind(focus = self.on_focus)

    max_char = 9
    def insert_text(self, substring, from_undo = False):
        if ((len(self.text) > self.max_char) and (self.max_char > 0)):
            substring = ""
        TextInput.insert_text(self, substring, from_undo)
    
    def on_focus(self, instance, value):
        if value:
            print('User focused', instance)
        else:
            print('User unfocused', instance)
            self.validate_format()
    
    def validate_format(self):
        text_raw = self.text

        # removes unwanted characters
        text_cleaned = ''.join(filter(lambda x: x in '0123456789', text_raw))
        if (len(text_cleaned) == 10):
            # formats input to (###) ###-####
            self.text = f"({text_cleaned[:3]}) {text_cleaned[3:6]}-{text_cleaned[6:]}"

class MainLayout(Widget):
    name = ObjectProperty(None)
    age_range = ObjectProperty(None)
    genders_list = []
    phone_number = ObjectProperty(None)

    # dictionary for data
    data = {
        'name': None,
        'age_range': None,
        'gender': None,
        'phone_number': None
    }

    def checkbox_click(self, instance, value, gender):
        if value is True:
            MainLayout.genders_list.append(gender)
        else:
            MainLayout.genders_list.remove(gender)

    def submit_data(self):
        name = self.name.text
        age_range = self.age_range.text
        phone_number = self.phone_number.text

        self.data['name'] = name
        self.data['age_range'] = age_range
        self.data['gender'] = MainLayout.genders_list
        self.data['phone_number'] = phone_number

        if (name != '' and age_range != 'Select Age' and
            len(MainLayout.genders_list) != 0 and phone_number != ''
            and len(phone_number) == 14):
            print(self.data)
            App.get_running_app().stop()
        else:
            print("Invalid Inputs")

# main class to run
class MainApp(App):
    def build(self):
        Window.clearcolor = ((77/255), (77/255), (77/255), 1)
        self.title = 'Demographics'
        return MainLayout()

if __name__ == '__main__':
    MainApp().run()