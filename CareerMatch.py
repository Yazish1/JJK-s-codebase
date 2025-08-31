from kivy.config import Config
Config.set('graphics', 'width', '100')
Config.set('graphics', 'height', '175')
Config.set('graphics', 'resizable', False)

from kivy.core.window import Window

# Force exact window size in pixels (overrides DPI scaling)
# Set fixed size
Window.size = (400, 700)
Window.minimum_width = Window.width
Window.minimum_height = Window.height
Window.maximum_width = Window.width
Window.maximum_height = Window.height

# Center the window on screen
screen_width, screen_height = Window.system_size
Window.left = (screen_width - Window.width) // 2
Window.top = (screen_height - Window.height) // 2

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle, PushMatrix, PopMatrix, Translate, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.properties import ListProperty, ColorProperty
from kivy.metrics import dp

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")

# --- Database Management ---
class DatabaseManagement:
    def __init__(self, db_path):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shortlist (
                    user_id INTEGER,
                    job_rowid INTEGER,
                    UNIQUE(user_id, job_rowid)
                )
            ''')
            db.commit()

    def create_user(self, username, password):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}');")
                db.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username, password):
        with sqlite3.connect(self.db_path) as db:
            cursor = db.cursor()
            cursor.execute(f"SELECT id FROM users WHERE username='{username}' AND password='{password}';")
            result = cursor.fetchone()
            return result[0] if result else None

# --- Screens ---
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print(Window.width)
        print(Window.height)

        self.discoverScroll = ScrollView(
            size_hint=(0.875, 0.214),
            pos_hint={"center_x": 0.5, "top": 0.85}
        )
        self.discoverLayout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            padding=(dp(100), 0, dp(100),0),
            spacing=400
        )
        self.discoverLayout.bind(minimum_width=self.discoverLayout.setter('width'))
        self.discoverScroll.add_widget(self.discoverLayout)
        self.add_widget(self.discoverScroll)

        self.shortlistScroll = ScrollView(
            size_hint=(0.875, 0.321),
            pos_hint={"center_x": 0.5, "y": 0.25}
        )
        self.shortlistLayout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            padding=(dp(100), 0, dp(100),0),
            spacing=400,
        )
        self.shortlistLayout.bind(minimum_width=self.shortlistLayout.setter('width'))
        self.shortlistScroll.add_widget(self.shortlistLayout)
        self.add_widget(self.shortlistScroll)

        
    def on_pre_enter(self):
        print(f"home: {App.get_running_app().user_id}")
        self.discoverLayout.clear_widgets()
        self.shortlistLayout.clear_widgets()

        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            cursor.execute("SELECT Job_Title, Company_Name, Benefits, Industry_Tag FROM listings;")
            result = cursor.fetchall()

        for job in result:
            lbl = Label(
                text=f"Job: {job[0]}\nCompany: {job[1]}\nWage: {job[2]}\nIndustry: {job[3]}",
                size_hint_x=None,
                width=0.1875 * self.width,   # 150/800
                color=(0, 0, 0, 1),
                valign='middle',
                halign='left'
            )
            self.discoverLayout.add_widget(lbl)

        with sqlite3.connect(DB_PATH) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT s.job_name, l.Company_Name, l.Benefits, l.Industry_Tag from shortlisted as s inner join listings as l on s.job_name = l.Job_Title WHERE s.user_id = '{App.get_running_app().user_id}';")
                self.result = cursor.fetchall()

        for i in range(len(self.result)):
            lbl = Label(
                text=f"job: {self.result[i][0]}\ncompany: {self.result[i][1]}\nwage: {self.result[i][2]}\nindustry: {self.result[i][3]}\n",
                size_hint_x=None,
                width=0.1875 * self.width,   # 150/800
                color=(0, 0, 0, 1),
                valign='middle',
                halign='left')
            self.shortlistLayout.add_widget(lbl)


class AccountScreen(Screen):
    def toHome(self):
        self.manager.current = "HomeScreen"

class ShortlistScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scroll = ScrollView(
            size_hint=(None, None),
            size_hint_y=None,
            size=(700, 1025),
            pos=(50, 175)
        )

        # Layout inside the scroll view
        self.layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=(0, dp(60), 0, dp(60)),
            spacing=200,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))  # important for scrolling
        self.scroll.add_widget(self.layout)
        self.add_widget(self.scroll)
        
    def on_pre_enter(self):
        self.layout.clear_widgets()
        with sqlite3.connect(DB_PATH) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT s.job_name, l.Company_Name, l.Benefits, l.Industry_Tag from shortlisted as s inner join listings as l on s.job_name = l.Job_Title WHERE s.user_id = '{App.get_running_app().user_id}';")
                self.result = cursor.fetchall()

        # Add many labels
        for i in range(len(self.result)):
            lbl = Label(text=f"job: {self.result[i][0]}\ncompany: {self.result[i][1]}\nwage: {self.result[i][2]}\nindustry: {self.result[i][3]}\n", size_hint_y=None, height=40, color=(0, 0, 0, 1))
            self.layout.add_widget(lbl)

        # Add the scroll view to the screen
        self.scroll.scroll_y = 1

class SwipingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_x = 0
        self.start_y = 0
        self.index = -1

        self.card = FloatLayout()

        with sqlite3.connect(DB_PATH) as db:
            cursor = db.cursor()
            cursor.execute(f"SELECT Job_Title, Company_Name, Benefits, Industry_Tag FROM listings;")
            self.result = cursor.fetchall()
            print(self.result)
        
        self.lbl = Label(
            text=f"Job: {self.result[self.index][0]}\nCompany: {self.result[self.index][1]}\nWage: {self.result[self.index][2]}\nIndustry: {self.result[self.index][3]}",
            halign='center',
            valign='middle',
            size_hint=(None, None),
            size=(400, 200),  # give it a visible size
            pos=(200, 700),
            color=(0, 0, 0, 1)
        )

        # Allow halign/valign to work
        self.lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        self.card.add_widget(self.lbl)
        self.add_widget(self.card)
            

    # Skip or like job ------------------------------------------
    def skip_job(self):
        pass

    def like_job(self): #-------------------------------------------------
        pass


    def on_touch_down(self, touch):
        self.start_x = touch.x
        self.start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        dx = touch.x - self.start_x
        dy = touch.y - self.start_y

        if abs(dx) > abs(dy):
            if self.index >= 0:
                if dx > 5:
                    print("Swipe Right")
                    with sqlite3.connect(DB_PATH) as db:
                        cursor = db.cursor()
                        cursor.execute(f"INSERT INTO shortlisted (user_id, job_name) VALUES ('{App.get_running_app().user_id}', '{self.result[self.index][0]}');")
                        print(App.get_running_app().user_id)
                        print("inserting")
                        db.commit()
                elif dx < -5:
                    print("Swipe Left")
                self.index+=1
                if self.index >= len(self.result):
                    self.lbl.text = "No more jobs"
                else:
                    self.lbl.text = f"Job: {self.result[self.index][0]}\nCompany: {self.result[self.index][1]}\nWage: {self.result[self.index][2]}\nIndustry: {self.result[self.index][3]}"
            else:
                self.index+=1

class ListingScreen(Screen):
    def toHome(self):
        self.manager.current = "HomeScreen"

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username_input = TextInput(hint_text="Username", size_hint=(None,None), size=(400,50), pos=(200,900))
        self.password_input = TextInput(hint_text="Password", password=True, size_hint=(None,None), size=(400,50), pos=(200,800))
        self.message = Label(text="", pos=(200, 700), size_hint=(None,None), size=(400,50), color=(1,0,0,1))
        login_btn = Button(text="Login", size_hint=(None,None), size=(200,50), pos=(300,650), on_press=self.login)
        self.add_widget(self.username_input)
        self.add_widget(self.password_input)
        self.add_widget(login_btn)
        self.add_widget(self.message)

    def login(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        userID = self.manager.db_manager.authenticate_user(username, password)
        if userID:
            #self.manager.user_id = userID
            self.manager.current = "HomeScreen"
            App.get_running_app().user_id = userID
            print(App.get_running_app().user_id)

        else:
            self.message.text = "Invalid credentials"

# --- Main App ---
class CareerMatch(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.db_manager = DatabaseManagement(DB_PATH)
        self.user_id = 0
        # Add all screens
        self.sm.add_widget(HomeScreen(name="HomeScreen"))
        self.sm.add_widget(AccountScreen(name="AccountScreen"))
        self.sm.add_widget(ShortlistScreen(name="ShortlistScreen"))
        self.sm.add_widget(SwipingScreen(name="SwipingScreen"))
        self.sm.add_widget(ListingScreen(name="ListingScreen"))
        self.sm.add_widget(LoginScreen(name="LoginScreen"))
        return self.sm

    def toHome(self):
        print(Window.width)
        print(Window.height)
        self.sm.current = "HomeScreen"

    def toAccount(self):
        self.sm.current = "AccountScreen"

    def toShortlist(self):
        self.sm.current = "ShortlistScreen"

    def toSwiping(self):
        self.sm.current = "SwipingScreen"

    def toListing(self):
        self.sm.current = "ListingScreen"
    
    def toLogin(self):
        self.sm.current = "LoginScreen"

if __name__ == '__main__':
    CareerMatch().run()
