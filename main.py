import os
import sys
import json
import math
import random

# --- 1. CONFIGURATION ---
from kivy.config import Config
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.image import AsyncImage
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.utils import get_color_from_hex, get_hex_from_color, platform

# --- OPTIONAL DEPENDENCIES ---
try:
    from plyer import notification
except ImportError:
    notification = None

try:
    from PIL import Image as PILImage, ImageStat
except ImportError:
    PILImage = None

# --- CONSTANTS ---
YELLOW = "#f7f5dd"

# --- FONT SELECTION LOGIC ---
FONT_NAME = "Roboto-Regular"

FONT_MAP = {
    "Regular": "Roboto-Regular",
    "Italic": "Roboto-Italic",
    "Bold": "Roboto-Bold",
    "Bold Italic": "Roboto-BoldItalic"
}

FONT_SIZES = {
    "Small": 1.0,
    "Medium": 1.075,
    "Large": 1.15
}

# --- HELPER FUNCTIONS ---
def resource_path(relative_path):
    """Resolve a resource path both in development and in a PyInstaller bundle."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_luminance(color_list):
    """Return the perceived luminance (0-1) of an RGB(A) color list."""
    r, g, b = color_list[:3]
    return (0.299 * r + 0.587 * g + 0.114 * b)

# --- FILE PATH MANAGEMENT ---
def get_user_data_dir():
    """Return a writable directory for persistent app data on each platform."""
    if platform == 'android' or platform == 'ios':
        return App.get_running_app().user_data_dir
    else:
        return os.path.dirname(os.path.abspath(__file__))

# --- KV DESIGN ---
KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<TkButton@Button>:
    background_normal: ''
    background_down: ''
    background_disabled_normal: ''
    background_color: 0,0,0,0
    color: app.btn_fg_color
    font_name: app.font_name_global
    font_size: 13 * app.font_scale
    size_hint: None, None
    height: 35 * app.font_scale
    
    canvas.before:
        Color:
            rgba: app.btn_bg_color if self.state == 'normal' else app.btn_bg_pressed
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
            
    canvas.after:
        Color:
            rgba: app.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 15)
            width: 0.7 

<TkInput@TextInput>:
    multiline: False
    input_filter: 'int' 
    size_hint: None, None
    height: 22 * app.font_scale
    width: 45 * app.font_scale
    font_name: app.font_name_global
    font_size: 13 * app.font_scale
    
    background_normal: ''
    background_active: ''
    background_color: app.btn_bg_color 
    foreground_color: app.btn_fg_color
    cursor_color: app.btn_fg_color
    
    padding_y: [self.height / 2.0 - (self.line_height / 2.0), 0]
    
    on_text_validate: app.root.instant_save(self)
    on_focus: if not self.focus: app.root.instant_save(self)
    
    canvas.after:
        Color:
            rgba: app.border_color
        Line:
            rectangle: self.x, self.y, self.width, self.height
            width: 0.7

<TaskItem>:
    size_hint_y: None
    height: 60 * app.font_scale
    orientation: 'vertical'
    padding: [0, 5, 0, 5]
    
    Label:
        text: root.task_label
        font_name: app.font_name_global
        font_size: 11 * app.font_scale
        color: app.text_color
        size_hint_y: None
        height: 15 * app.font_scale
        halign: 'left'
        text_size: self.size

    BoxLayout:
        orientation: 'horizontal'
        spacing: 10
        size_hint_y: None
        height: 35 * app.font_scale
        
        TextInput:
            id: task_input
            text: root.task_text
            multiline: False
            font_name: app.font_name_global
            font_size: 13 * app.font_scale
            
            background_normal: ''
            background_active: ''
            background_color: app.btn_bg_color 
            foreground_color: app.btn_fg_color
            cursor_color: app.btn_fg_color

            padding_y: [self.height / 2.0 - (self.line_height / 2.0), 0]
            on_text_validate: root.save_changes()
            on_focus: if not self.focus: root.save_changes()
            
            canvas.after:
                Color:
                    rgba: app.border_color
                Line:
                    rectangle: self.x, self.y, self.width, self.height
                    width: 0.7

        CheckBox:
            id: task_check
            active: root.is_done
            size_hint_x: None
            width: 30 * app.font_scale
            color: app.text_color
            on_active: root.save_changes()
            canvas.before:
                Color: 
                    rgba: app.text_color
        
        Button:
            text: "X"
            size_hint_x: None
            width: 30 * app.font_scale
            background_color: 0,0,0,0
            color: (1, 0.3, 0.3, 1)
            bold: True
            font_name: app.font_name_global
            on_release: root.delete_self()
            canvas.before:
                Color:
                    rgba: (1, 0.8, 0.8, 0.2)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [5]

<TasksPopupContent>:
    orientation: 'vertical'
    spacing: 10
    padding: 15
    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

<TaskAddButton>:
    background_normal: ''
    background_down: ''
    background_disabled_normal: ''
    background_color: 0,0,0,0
    color: app.btn_fg_color
    font_name: app.font_name_global
    font_size: 13 * app.font_scale
    size_hint_y: None
    height: 40 * app.font_scale
    
    canvas.before:
        Color:
            rgba: app.btn_bg_color if self.state == 'normal' else app.btn_bg_pressed
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
    canvas.after:
        Color:
            rgba: app.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 15)
            width: 0.7 

<PopupCloseButton>:
    background_normal: ''
    background_down: ''
    background_color: 0,0,0,0
    color: app.btn_fg_color
    bold: True
    font_name: app.font_name_global
    font_size: 14 * app.font_scale
    size_hint: None, None
    size: 35 * app.font_scale, 35 * app.font_scale
    canvas.before:
        Color:
            rgba: app.btn_bg_color if self.state == 'normal' else app.btn_bg_pressed
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [10]
    canvas.after:
        Color:
            rgba: app.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 10)
            width: 0.7

<GalleryItem>:
    orientation: 'vertical'
    size_hint: None, None
    size: 110 * app.font_scale, 130 * app.font_scale
    padding: 5
    
    canvas.before:
        Color:
            rgba: (0,0,0,0.05) if self.state == 'normal' else (0,0,0,0.1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [8]

    AnchorLayout:
        size_hint_y: 0.75
        AsyncImage:
            source: root.thumbnail_source
            allow_stretch: True
            keep_ratio: True
            nocache: True
            size_hint: None, None
            size: (self.parent.width * 0.9, self.parent.height * 0.9)

    Label:
        text: root.filename
        font_name: app.font_name_global
        font_size: 10 * app.font_scale
        color: app.text_color
        text_size: (self.width - 10, None)
        short: True
        shorten_from: 'right'
        halign: 'center'
        valign: 'middle'
        size_hint_y: 0.25

<DarkToggle@ToggleButton>:
    background_normal: ''
    background_down: ''
    size_hint: None, None
    size: 60 * app.font_scale, 28 * app.font_scale
    background_color: 0, 0, 0, 0 
    state: 'down' if app.is_dark_mode else 'normal'
    on_release: app.toggle_dark_mode()
    canvas:
        Color:
            rgba: app.btn_bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [14]
        Color:
            rgba: app.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 14)
            width: 0.7
        Color:
            rgba: (1, 1, 0, 1) if self.state == 'normal' else (0.9, 0.9, 1, 1)
        Ellipse:
            pos: (self.x + 4, self.y + 4) if self.state == 'normal' else (self.right - self.height + 4, self.y + 4)
            size: self.height - 8, self.height - 8

<TkCheckBox@CheckBox>:
    size_hint: None, None
    size: 30 * app.font_scale, 30 * app.font_scale
    color: app.text_color
    canvas.before:
        Color:
            rgba: 0,0,0,0

<TkSpinner@Spinner>:
    background_normal: ''
    background_down: ''
    background_color: 0,0,0,0
    color: app.btn_fg_color
    font_name: app.font_name_global
    font_size: 13 * app.font_scale
    size_hint: None, None
    height: 30 * app.font_scale
    width: 80 * app.font_scale
    
    canvas.before:
        Color:
            rgba: app.btn_bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [15]
            
    canvas.after:
        Color:
            rgba: app.border_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, 15)
            width: 0.7
    option_cls: 'TkSpinnerOption'

<TkSpinnerOption@SpinnerOption>:
    background_normal: ''
    background_color: 0.9, 0.9, 0.9, 1
    color: 0, 0, 0, 1
    font_name: app.font_name_global
    height: 30

# --- MAIN LAYOUT ---
<PomodoroLayout>:
    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    # --- TOP SECTION ---
    BoxLayout:
        orientation: 'vertical'
        pos_hint: {'top': 1.0, 'x': 0}
        size_hint_y: None
        height: '380dp'
        padding: [0, 0, 0, 20]
        spacing: 0

        Label:
            text: root.title_text
            font_name: app.font_name_global
            font_size: 25 * app.font_scale
            bold: True
            color: app.text_color
            size_hint_y: None
            height: 35 * app.font_scale

        Widget: 
            size_hint_y: None
            height: 8

        FloatLayout:
            size_hint_y: None
            height: '240dp' 
            
            FloatLayout:
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                size_hint: None, None
                size: ('240dp', '240dp')
                
                Image:
                    id: img_loader
                    source: root.image_source
                    opacity: 0
                    allow_stretch: True
                    keep_ratio: False 

                Widget:
                    size_hint: 1, 1
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    on_touch_down: if self.collide_point(*args[1].pos): root.on_image_click(args[1])

                    canvas.before:
                        Color:
                            rgba: 1, 1, 1, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [25,]
                            texture: img_loader.texture

            Label:
                id: timer_label
                text: root.timer_text
                font_name: app.font_name_global
                font_size: 32 * app.font_scale
                bold: True
                color: app.timer_color
                pos_hint: {'center_x': 0.5, 'center_y': 0.45}
                canvas.before:
                    Color:
                        rgba: (0,0,0,0.4) if app.timer_color == get_color_from_hex('#ffffff') else (1,1,1,0.4)
                    RoundedRectangle:
                        pos: self.center_x - (self.texture_size[0]/2 + 10), self.center_y - (self.texture_size[1]/2 + 5)
                        size: self.texture_size[0] + 20, self.texture_size[1] + 10
                        radius: [10]

        Widget: 
            size_hint_y: None
            height: 8

        Label:
            text: root.message_text
            font_name: app.font_name_global
            font_size: 13 * app.font_scale
            color: app.text_color
            size_hint_y: None
            height: 40 * app.font_scale
            halign: 'center'
            valign: 'top'
            text_size: self.width, None
            markup: True

    # --- BOTTOM SECTION ---
    BoxLayout:
        orientation: 'vertical'
        pos_hint: {'x': 0, 'y': 0}
        size_hint_y: None
        height: self.minimum_height
        padding: [20, 10, 20, 10]
        spacing: 10 

        # CONTROL BUTTONS
        BoxLayout:
            size_hint_y: None
            height: 40 * app.font_scale
            spacing: 10 
            orientation: 'horizontal'
            Widget: 
            TkButton:
                text: "Start"
                width: 90 * app.font_scale
                on_release: root.start_timer()
            TkButton:
                text: root.pause_label
                width: 90 * app.font_scale
                on_release: root.toggle_pause()
            TkButton:
                text: "Stop"
                width: 90 * app.font_scale
                on_release: root.stop_timer()
            Widget:

        # INPUT FIELDS
        BoxLayout:
            spacing: 10
            size_hint_y: None
            height: 25 * app.font_scale
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: self.minimum_width
            
            Label: 
                text: "Work:"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size
            TkInput:
                id: input_work
            Label:
                text: " S.Break:"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size
            TkInput:
                id: input_short
            Label:
                text: " L.Break:"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size
            TkInput:
                id: input_long

        BoxLayout:
            spacing: 10
            size_hint_y: None
            height: 35 * app.font_scale
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: self.minimum_width
            
            TkButton:
                text: "BG Color"
                width: 100 * app.font_scale
                on_release: root.open_color_picker()
            TkButton:
                text: "Image"
                width: 100 * app.font_scale
                on_release: root.open_file_chooser()
            TkButton:
                text: "Reset"
                width: 100 * app.font_scale
                on_release: root.reset_theme()

        BoxLayout:
            spacing: 10
            size_hint_y: None
            height: 30 * app.font_scale
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: self.minimum_width
            
            Label:
                text: "Font: "
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size

            TkSpinner:
                id: font_spinner
                text: root.settings.get('font_style', 'Regular')
                values: ['Regular', 'Italic', 'Bold', 'Bold Italic']
                on_text: root.update_setting('font_style', self.text)
                width: 100 * app.font_scale 

            Label:
                text: "  UI Size: "
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size
            
            TkSpinner:
                id: ui_spinner
                text: root.settings.get('font_size', 'Medium')
                values: ['Small', 'Medium', 'Large']
                on_text: root.update_setting('font_size', self.text)
                width: 80 * app.font_scale

        BoxLayout:
            spacing: 10
            size_hint_y: None
            height: 35 * app.font_scale
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: self.minimum_width
            
            Label:
                text: "Light Mode"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 13 * app.font_scale
                size_hint: None, None
                size: self.texture_size
                valign: 'middle'

            DarkToggle:
                id: dark_toggle
            
            Label:
                text: "Dark Mode"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 13 * app.font_scale
                size_hint: None, None
                size: self.texture_size
                valign: 'middle'

        BoxLayout:
            spacing: 10
            size_hint_y: None
            height: 30 * app.font_scale
            pos_hint: {'center_x': 0.5}
            size_hint_x: None
            width: self.minimum_width

            TkCheckBox:
                active: root.settings.get('sound_enabled', True)
                on_active: root.update_setting('sound_enabled', args[1])
            Label:
                text: "Sound "
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size
            
            TkCheckBox:
                active: root.settings.get('popup_enabled', True)
                on_active: root.update_setting('popup_enabled', args[1])
            Label:
                text: "Notify"
                color: app.text_color
                font_name: app.font_name_global
                font_size: 14 * app.font_scale
                size_hint: None, None
                size: self.texture_size

        BoxLayout:
            size_hint_y: None
            height: 50 * app.font_scale
            spacing: 10
            padding: [20, 0 , 20, 5]
            
            Label:
                text: root.total_time_text
                font_size: 12 * app.font_scale
                font_name: app.font_name_global
                color: app.text_color
                halign: 'left'
                valign: 'middle'
                size_hint_x: 0.4
                text_size: self.size 
            
            TkButton:
                text: "Reset Stats"
                width: 110 * app.font_scale
                on_release: root.reset_stats()
                
            TkButton:
                text: "Tasks"
                width: 70 * app.font_scale
                on_release: root.open_tasks_popup()
"""

# --- WIDGET CLASSES ---
class TaskItem(BoxLayout):
    """A single row in the task manager: label, text input, done checkbox, delete button."""
    task_label = StringProperty("Task")
    task_text = StringProperty("")
    is_done = BooleanProperty(False)
    index = NumericProperty(0)
    
    def __init__(self, index, text, done, save_callback, delete_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback
        self.delete_callback = delete_callback
        self.index = index
        self.task_label = f"Task {index + 1}"
        self.task_text = text
        self.is_done = done
    
    def save_changes(self):
        if self.save_callback:
            self.task_text = self.ids.task_input.text
            self.is_done = self.ids.task_check.active
            self.save_callback()

    def delete_self(self):
        if self.delete_callback:
            self.delete_callback(self)

class TasksPopupContent(BoxLayout):
    pass

class TaskAddButton(Button):
    pass

class PopupCloseButton(Button):
    pass

class GalleryItem(ButtonBehavior, BoxLayout):
    """A thumbnail tile in the image gallery popup (folder or image file)."""
    filename = StringProperty("")
    thumbnail_source = StringProperty("")
    is_folder = BooleanProperty(False)
    full_path = StringProperty("")
    
    def __init__(self, path, filename, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.full_path = os.path.join(path, filename)
        self.filename = filename
        
        if os.path.isdir(self.full_path):
            self.is_folder = True
            self.thumbnail_source = 'atlas://data/images/defaulttheme/filechooser_folder'
        else:
            self.is_folder = False
            self.thumbnail_source = self.full_path

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if platform not in ('android', 'ios'):
                if touch.is_double_tap:
                    self.callback(self.full_path, self.is_folder)
                    return True
        return super().on_touch_down(touch)

    def on_release(self):
        if platform in ('android', 'ios'):
            self.callback(self.full_path, self.is_folder)

class PomodoroLayout(FloatLayout):
    """Root widget: timer logic, settings persistence, theming, tasks and gallery popups."""
    title_text = StringProperty("Timer")
    timer_text = StringProperty("00:00")
    message_text = StringProperty("")
    check_marks = StringProperty("")
    total_time_text = StringProperty("Total Time:\n0h:0min")
    pause_label = StringProperty("Pause")
    image_source = StringProperty(resource_path("tomato.png"))
    
    settings = {}
    
    reps = 0
    timer_event = None
    is_paused = False
    is_running = False
    current_seconds = 0
    session_minutes = 0
    files = {}
    is_loading_tasks = False

    def __init__(self, **kwargs):
        self.initialize_files()
        self.load_settings()
        super().__init__(**kwargs)
        self.load_total_stats()
        self.apply_theme()
        Clock.schedule_once(self.update_inputs_manually, 0)

        # Warn about missing bundled assets (app still runs without them)
        if not os.path.exists(self.image_source):
            print(f"Warning: image not found: {self.image_source}")
        if not os.path.exists(self.files["sound"]):
            print(f"Warning: sound not found: {self.files['sound']}")

    def initialize_files(self):
        data_dir = get_user_data_dir()
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except OSError:
                pass

        self.files = {
            "total": os.path.join(data_dir, "work_total.txt"),
            "settings": os.path.join(data_dir, "settings.json"),
            "tasks": os.path.join(data_dir, "tasks.json"),
            "sound": resource_path("bell.wav")
        }

    def load_settings(self):
        default = {
            "work_min": 25, "short_break": 5, "long_break": 30, 
            "dark_mode": False, "font_size": "Medium",
            "font_style": "Regular",
            "sound_enabled": True, "popup_enabled": True, 
            "light_bg": YELLOW, "custom_image": "tomato.png"
        }
        
        loaded = default.copy()
        if os.path.exists(self.files["settings"]):
            try:
                with open(self.files["settings"], "r") as f:
                    loaded.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass
        
        # Sanitize numeric settings in case the file was edited by hand
        try:
            loaded['work_min'] = int(loaded['work_min'])
        except (ValueError, TypeError):
            loaded['work_min'] = 25
        try:
            loaded['short_break'] = int(loaded['short_break'])
        except (ValueError, TypeError):
            loaded['short_break'] = 5
        try:
            loaded['long_break'] = int(loaded['long_break'])
        except (ValueError, TypeError):
            loaded['long_break'] = 30
            
        self.settings = loaded
        
        app = App.get_running_app()
        if app:
            app.is_dark_mode = self.settings.get('dark_mode', False)
            self.update_font_scale()
            self.update_font_style()
    
    def update_inputs_manually(self, dt=None):
        self.ids.input_work.text = str(self.settings['work_min'])
        self.ids.input_short.text = str(self.settings['short_break'])
        self.ids.input_long.text = str(self.settings['long_break'])

    def save_settings(self):
        with open(self.files["settings"], "w") as f:
            json.dump(self.settings, f)

    def instant_save(self, input_widget):
        """Validate a duration input, clamp it to allowed limits and persist it."""
        try:
            safe_text = ''.join(filter(str.isdigit, input_widget.text))
            if not safe_text:
                raise ValueError
            val = int(safe_text)
            
            w_id = self.ids.input_work
            s_id = self.ids.input_short
            l_id = self.ids.input_long
            
            warning_msg = None

            if input_widget == w_id:
                if val < 10: 
                    val = 10
                    warning_msg = "Work time cannot be less than 10 min."
                if val > 120: 
                    val = 120
                    warning_msg = "Work time cannot exceed 120 min."
                self.settings['work_min'] = val
            elif input_widget == s_id:
                if val < 5: 
                    val = 5
                    warning_msg = "Short break cannot be less than 5 min."
                if val > 20: 
                    val = 20
                    warning_msg = "Short break cannot exceed 20 min."
                self.settings['short_break'] = val
            elif input_widget == l_id:
                if val < 30: 
                    val = 30
                    warning_msg = "Long break cannot be less than 30 min."
                if val > 60: 
                    val = 60
                    warning_msg = "Long break cannot exceed 60 min."
                self.settings['long_break'] = val
            
            input_widget.text = str(val)
            self.save_settings()

            if warning_msg:
                self.show_popup("Input Limit", warning_msg)
            
        except ValueError:
            if input_widget == self.ids.input_work:
                input_widget.text = str(self.settings['work_min'])
            elif input_widget == self.ids.input_short:
                input_widget.text = str(self.settings['short_break'])
            elif input_widget == self.ids.input_long:
                input_widget.text = str(self.settings['long_break'])

    def update_font_scale(self):
        size_key = self.settings.get("font_size", "Medium")
        app = App.get_running_app()
        if app:
            app.font_scale = FONT_SIZES.get(size_key, 1.0)
            
    def update_font_style(self):
        style_key = self.settings.get("font_style", "Regular")
        app = App.get_running_app()
        if app:
            app.font_name_global = FONT_MAP.get(style_key, "Roboto-Regular")

    def load_total_stats(self):
        total = 0
        if os.path.exists(self.files["total"]):
            try:
                with open(self.files["total"], "r") as f:
                    total = int(f.read().strip())
            except (ValueError, OSError):
                pass
        self.update_total_label(total)

    def save_total_stats(self, minutes_to_add):
        current = 0
        if os.path.exists(self.files["total"]):
            try: 
                with open(self.files["total"], "r") as f: 
                    current = int(f.read().strip())
            except (ValueError, OSError):
                pass
        new_total = current + minutes_to_add
        with open(self.files["total"], "w") as f:
            f.write(str(new_total))
        self.update_total_label(new_total)

    def update_total_label(self, total_minutes):
        self.total_time_text = f"Total Time:\n{total_minutes // 60}h:{total_minutes % 60}min"

    def apply_theme(self):
        """Recompute all theme colors based on current background and image settings."""
        app = App.get_running_app()
        if not app:
            return

        if app.is_dark_mode:
            app.bg_color = get_color_from_hex("#2e2e2e")
        else:
            app.bg_color = get_color_from_hex(self.settings['light_bg'])
        
        luminance = get_luminance(app.bg_color)
        if luminance < 0.6:
            app.text_color = get_color_from_hex("#ffffff")
        else:
            app.text_color = get_color_from_hex("#000000")

        if luminance < 0.05: 
            app.border_color = [0.5, 0.5, 0.5, 1] 
        else:
            app.border_color = [0, 0, 0, 1] 

        r, g, b, a = app.bg_color
        
        if luminance < 0.05: 
            app.btn_bg_color = [0.25, 0.25, 0.25, 1] 
            app.btn_bg_pressed = [0.35, 0.35, 0.35, 1]
        elif luminance < 0.5: 
            app.btn_bg_color = [min(r + 0.15, 1.0), min(g + 0.15, 1.0), min(b + 0.15, 1.0), 1]
            app.btn_bg_pressed = [min(r + 0.25, 1.0), min(g + 0.25, 1.0), min(b + 0.25, 1.0), 1]
        else: 
            app.btn_bg_color = [r * 0.85, g * 0.85, b * 0.85, 1]
            app.btn_bg_pressed = [r * 0.75, g * 0.75, b * 0.75, 1]

        btn_lum = get_luminance(app.btn_bg_color)
        if btn_lum < 0.6:
            app.btn_fg_color = get_color_from_hex("#ffffff")
        else:
            app.btn_fg_color = get_color_from_hex("#000000")

        img_path = self.settings['custom_image']
        if img_path == "tomato.png":
            img_path = resource_path("tomato.png")
        
        self.image_source = img_path

        # Pick a timer text color that stays readable on top of the chosen image
        app.timer_color = app.text_color
        if PILImage and os.path.exists(self.image_source):
            try:
                img = PILImage.open(self.image_source).convert('L')
                stat = ImageStat.Stat(img)
                if stat.mean[0] > 140:
                    app.timer_color = get_color_from_hex("#000000")
                else:
                    app.timer_color = get_color_from_hex("#ffffff")
            except (OSError, ValueError):
                pass

    def reset_theme(self):
        app = App.get_running_app()
        self.settings['light_bg'] = YELLOW
        self.settings['custom_image'] = "tomato.png"
        app.is_dark_mode = False 
        self.settings['dark_mode'] = False
        self.settings['font_size'] = "Medium"
        self.settings['font_style'] = "Regular"
        self.save_settings()
        
        self.update_font_scale()
        self.update_font_style()
        self.apply_theme()
        
        if 'font_spinner' in self.ids:
            self.ids.font_spinner.text = "Regular"
        if 'ui_spinner' in self.ids:
            self.ids.ui_spinner.text = "Medium"

    def start_timer(self):
        """Start the next Pomodoro phase (work / short break / long break)."""
        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False
        self.pause_label = "Pause"
        self.reps += 1
        self.session_minutes = 0

        work_sec = int(self.settings['work_min']) * 60
        short_sec = int(self.settings['short_break']) * 60
        long_sec = int(self.settings['long_break']) * 60

        if self.reps % 8 == 0:
            self.count_down(long_sec)
            self.title_text = "Break"
            self.message_text = "Long Break! Resetting marks."
            self.check_marks = ""
        elif self.reps % 2 == 0:
            self.count_down(short_sec)
            self.title_text = "Break"
            self.message_text = "Take a short break."
        else:
            self.count_down(work_sec)
            self.title_text = "Work"
            quotes = ["You've got this!", "Believe in yourself", "Keep pushing!", "Stay focused!"]
            self.message_text = random.choice(quotes)

    def count_down(self, count):
        self.current_seconds = count
        self.update_timer_display(count)
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_tick, 1)

    def update_tick(self, dt):
        if self.current_seconds > 0:
            self.current_seconds -= 1
            self.update_timer_display(self.current_seconds)
            # During work sessions, log each completed minute to the stats file
            if self.reps % 2 != 0:
                elapsed = (int(self.settings['work_min']) * 60) - self.current_seconds
                if elapsed > 0 and elapsed % 60 == 0:
                    self.save_total_stats(1)
                    self.session_minutes += 1
        else:
            self.timer_event.cancel()
            self.is_running = False
            if self.reps % 2 != 0:
                marks = "✓" * (math.ceil(self.reps / 2) % 5)
                self.check_marks = marks
            
            self.trigger_notification_and_sound()
            self.start_timer()

    def update_timer_display(self, count):
        hours = count // 3600
        mins = (count % 3600) // 60
        secs = count % 60
        if hours > 0:
            self.timer_text = f"{hours}:{mins:02d}:{secs:02d}"
        else:
            self.timer_text = f"{mins:02d}:{secs:02d}"

    def toggle_pause(self):
        if not self.is_running:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_label = "Pause"
            self.timer_event = Clock.schedule_interval(self.update_tick, 1)
        else:
            self.is_paused = True
            self.pause_label = "Resume"
            if self.timer_event:
                self.timer_event.cancel()

    def stop_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
        self.is_running = False
        self.reps = 0
        self.timer_text = "00:00"
        self.title_text = "Timer"
        self.check_marks = ""
        self.message_text = ""
        self.pause_label = "Pause"

    def trigger_notification_and_sound(self):
        """Notify the user that a phase finished, using the platform's best option."""
        is_mobile = platform in ('android', 'ios')
        sound_on = self.settings.get('sound_enabled', True)
        notify_on = self.settings.get('popup_enabled', True)

        if is_mobile:
            if notify_on:
                if notification:
                    try:
                        notification.notify(
                            title="Pomodoro",
                            message=self.title_text + " time!",
                            timeout=10
                        )
                    except Exception as e:
                        print(f"Notification failed: {e}")
            elif sound_on:
                self.play_sound_file()
        else:
            if sound_on:
                self.play_sound_file()
            
            if notify_on:
                try:
                    Window.restore()
                    Window.raise_window()
                except Exception:
                    pass

    def play_sound_file(self):
        if os.path.exists(self.files["sound"]):
            sound = SoundLoader.load(self.files["sound"])
            if sound:
                sound.play()

    def update_setting(self, key, value):
        self.settings[key] = value
        if key == 'font_size':
            self.update_font_scale()
        if key == 'font_style':
            self.update_font_style() 
        self.save_settings()

    def on_image_click(self, touch):
        pass

    def reset_stats(self):
        with open(self.files["total"], "w") as f:
            f.write("0")
        self.update_total_label(0)
        self.show_popup("Reset", "Stats cleared.")

    def show_popup(self, title, content):
        popup = Popup(title=title, content=Label(text=content), size_hint=(None, None), size=(300, 200))
        popup.open()

    def open_color_picker(self):
        content = BoxLayout(orientation='vertical')
        clr_picker = ColorPicker(color=get_color_from_hex(self.settings.get('light_bg', YELLOW)))
        btn_select = Button(text="Select", size_hint_y=None, height='40dp')
        content.add_widget(clr_picker)
        content.add_widget(btn_select)
        popup = Popup(title="Pick Background Color", content=content, size_hint=(0.9, 0.9))
        
        def on_select(instance):
            app = App.get_running_app()
            self.settings['light_bg'] = get_hex_from_color(clr_picker.color)
            app.is_dark_mode = False 
            self.settings['dark_mode'] = False
            self.save_settings()
            self.apply_theme()
            popup.dismiss()
            
        btn_select.bind(on_release=on_select)
        popup.open()

    def open_file_chooser(self):
        self.open_gallery_popup(os.path.dirname(os.path.abspath(__file__)))

    def open_gallery_popup(self, path):
        content = TasksPopupContent() 
        
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height='40dp', spacing=10)
        
        btn_up = TaskAddButton(text="< Back", size_hint_x=None, width='80dp')
        btn_up.bind(on_release=lambda x: self.navigate_up(path))
        
        lbl_path = Label(text=path[-30:], color=App.get_running_app().text_color, font_name=App.get_running_app().font_name_global) 
        
        btn_close = PopupCloseButton(text="X")
        
        header.add_widget(btn_up)
        header.add_widget(lbl_path)
        header.add_widget(btn_close)
        content.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.gallery_grid = GridLayout(cols=3, spacing=10, size_hint_y=None, padding=10)
        self.gallery_grid.bind(minimum_height=self.gallery_grid.setter('height'))
        
        self.populate_gallery(path)
        
        scroll.add_widget(self.gallery_grid)
        content.add_widget(scroll)

        self.gallery_popup = Popup(
            title="", 
            separator_height=0, 
            content=content, 
            size_hint=(0.95, 0.95),
            background_color=(0,0,0,0)
        )
        
        btn_close.bind(on_release=self.gallery_popup.dismiss)
        self.gallery_popup.open()

    def navigate_up(self, current_path):
        new_path = os.path.dirname(current_path)
        self.gallery_popup.dismiss()
        self.open_gallery_popup(new_path)

    def populate_gallery(self, path):
        self.gallery_grid.clear_widgets()
        
        try:
            items = os.listdir(path)
        except OSError as e:
            print(f"Error accessing {path}: {e}")
            return

        dirs = []
        images = []
        valid_ext = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

        for item in items:
            full = os.path.join(path, item)
            if os.path.isdir(full):
                dirs.append(item)
            elif any(item.lower().endswith(ext) for ext in valid_ext):
                images.append(item)
        
        for d in dirs:
            btn = GalleryItem(path, d, self.on_gallery_item_select)
            self.gallery_grid.add_widget(btn)
            
        for img in images:
            btn = GalleryItem(path, img, self.on_gallery_item_select)
            self.gallery_grid.add_widget(btn)

    def on_gallery_item_select(self, full_path, is_folder):
        if is_folder:
            self.gallery_popup.dismiss()
            self.open_gallery_popup(full_path)
        else:
            self.settings['custom_image'] = full_path
            self.save_settings()
            self.apply_theme()
            self.gallery_popup.dismiss()

    def open_tasks_popup(self):
        app = App.get_running_app()
        content = TasksPopupContent()
        
        header_height = 40 * app.font_scale
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=header_height, spacing=10)
        
        header = Label(
            text="Task Manager", 
            size_hint_x=1,
            bold=True, 
            color=app.text_color,
            font_name=app.font_name_global
        )
        
        close_btn = PopupCloseButton(text="X")
        
        header_layout.add_widget(header)
        header_layout.add_widget(close_btn)
        content.add_widget(header_layout)

        self.tasks_container = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.tasks_container.bind(minimum_height=self.tasks_container.setter('height'))
        
        scroll = ScrollView(size_hint=(1, 1), bar_width=10)
        scroll.add_widget(self.tasks_container)
        content.add_widget(scroll)

        add_btn = TaskAddButton(text="+ Add New Task", size_hint_x=0.5, pos_hint={'center_x': 0.5})
        add_btn.bind(on_release=lambda x: self.add_new_task())
        content.add_widget(add_btn)

        self.tasks_popup = Popup(
            title="", 
            separator_height=0, 
            content=content, 
            size_hint=(0.9, 0.9),
            background_color=(0,0,0,0) 
        )
        
        close_btn.bind(on_release=self.tasks_popup.dismiss)
        
        self.load_tasks_into_view()
        
        self.tasks_popup.open()

    def load_tasks_into_view(self):
        self.is_loading_tasks = True
        
        self.tasks_container.clear_widgets()
        tasks_data = []
        if os.path.exists(self.files['tasks']):
            try:
                with open(self.files['tasks'], 'r') as f:
                    tasks_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        
        for i, task in enumerate(tasks_data):
            self.create_task_widget(i, task.get('text', ''), task.get('done', False))
            
        self.is_loading_tasks = False

    def create_task_widget(self, index, text, done):
        item = TaskItem(index, text, done, self.save_tasks_from_view, self.delete_task)
        self.tasks_container.add_widget(item)

    def add_new_task(self):
        index = len(self.tasks_container.children) 
        self.create_task_widget(index, "", False)
        self.save_tasks_from_view() 

    def delete_task(self, task_widget):
        self.tasks_container.remove_widget(task_widget)
        self.refresh_task_indices()
        self.save_tasks_from_view()

    def refresh_task_indices(self):
        children = self.tasks_container.children
        for i, child in enumerate(reversed(children)):
            child.index = i
            child.task_label = f"Task {i + 1}"

    def save_tasks_from_view(self):
        if self.is_loading_tasks:
            return

        tasks_data = []
        for child in reversed(self.tasks_container.children):
            tasks_data.append({
                'text': child.ids.task_input.text,
                'done': child.ids.task_check.active
            })
        
        with open(self.files['tasks'], 'w') as f:
            json.dump(tasks_data, f)

class PomodoroApp(App):
    bg_color = ListProperty(get_color_from_hex(YELLOW))
    text_color = ListProperty(get_color_from_hex("#000000"))
    
    btn_bg_color = ListProperty(get_color_from_hex("#e2979c"))
    btn_bg_pressed = ListProperty(get_color_from_hex("#d17b80"))
    btn_fg_color = ListProperty(get_color_from_hex("#ffffff"))
    
    border_color = ListProperty([0, 0, 0, 1])
    
    timer_color = ListProperty(get_color_from_hex("#ffffff"))
    font_scale = NumericProperty(1.0)
    
    font_name_global = StringProperty(FONT_NAME)
    
    is_dark_mode = BooleanProperty(False)

    def build(self):
        self.title = "Pomodoro"
        self.icon = resource_path("tomato.png") 

        Builder.load_string(KV)
        return PomodoroLayout()

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.root.settings['dark_mode'] = self.is_dark_mode
        self.root.save_settings()
        self.root.apply_theme()

if __name__ == "__main__":
    PomodoroApp().run()