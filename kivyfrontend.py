from kivy.config import Config


# Force window size
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '500')
Config.set('graphics', 'resizable', False)

from kivy.core.window import Window

scale = Window.dpi / 96
Window.size = (int(400*scale), int(700*scale))

screen_width, screen_height = Window.system_size
Window.left = (screen_width - Window.width) // 2
Window.top = (screen_height - Window.height) // 2

import os
import sqlite3
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")

class Database:
    def create_table(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                phone TEXT
            )
        """)
        conn.commit()
        conn.close()

    def register_user(self, username, password, email, phone):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
            (username, password, email, phone)
        )
        conn.commit()
        conn.close()

    def authenticate_user(self, username, password):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username=? AND password=?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Login", font_size=32))
        self.username = TextInput(hint_text="Username", multiline=False)
        self.password = TextInput(hint_text="Password", password=True, multiline=False)
        login_btn = Button(text="Login", on_press=self.login)
        signup_btn = Button(text="Go to Sign Up", on_press=self.go_signup)
        self.message = Label()
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_btn)
        layout.add_widget(signup_btn)
        layout.add_widget(self.message)
        self.add_widget(layout)

    def login(self, instance):
        db = Database()
        if db.authenticate_user(self.username.text, self.password.text):
            self.manager.current = "home"
        else:
            self.message.text = "Invalid login"

    def go_signup(self, instance):
        self.manager.current = "signup"


class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Sign Up", font_size=32))
        self.username = TextInput(hint_text="Username", multiline=False)
        self.password = TextInput(hint_text="Password", password=True, multiline=False)
        self.email = TextInput(hint_text="Email", multiline=False)
        self.phone = TextInput(hint_text="Phone", multiline=False)
        signup_btn = Button(text="Sign Up", on_press=self.signup)
        back_btn = Button(text="Back to Login", on_press=self.go_login)
        self.message = Label()
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(self.email)
        layout.add_widget(self.phone)
        layout.add_widget(signup_btn)
        layout.add_widget(back_btn)
        layout.add_widget(self.message)
        self.add_widget(layout)

    def signup(self, instance):
        db = Database()
        try:
            db.register_user(
                self.username.text, self.password.text,
                self.email.text, self.phone.text
            )
            self.manager.current = "home"
        except Exception as e:
            self.message.text = f"Error: {e}"

    def go_login(self, instance):
        self.manager.current = "login"


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(Label(text="Welcome to CareerMatch!", font_size=32))
        self.add_widget(layout)


class CareerMatchApp(App):
    def build(self):
        db = Database()
        db.create_table()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(HomeScreen(name="home"))
        return sm


if __name__ == "__main__":
    CareerMatchApp().run()
