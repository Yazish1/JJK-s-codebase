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

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")
user_id = 0

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
                cursor.execute("INSERT INTO users (username, password) VALUES ('{username}', '{password}');")
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
            padding=5,
            spacing=400
        )
        self.discoverLayout.bind(minimum_width=self.discoverLayout.setter('width'))
        self.discoverScroll.add_widget(self.discoverLayout)
        self.add_widget(self.discoverScroll)

        self.shortlistScroll = ScrollView(
            size_hint=(0.875, 0.321),
            pos_hint={"center_x": 0.5, "y": 0.15}
        )
        self.shortlistLayout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            padding=10,
            spacing=400,
        )
        self.shortlistLayout.bind(minimum_width=self.shortlistLayout.setter('width'))
        self.shortlistScroll.add_widget(self.shortlistLayout)
        self.add_widget(self.shortlistScroll)

        
    def on_pre_enter(self):
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
                valign='center',
                halign='left'
            )
            self.discoverLayout.add_widget(lbl)

        with sqlite3.connect(DB_PATH) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT job_name from shortlisted WHERE user_id = '{user_id}';")
                self.result = cursor.fetchall()

        for i in range(len(self.result)):
            lbl = Label(text=f"{self.result[i][0]}", size_hint_y=None, height=40, color=(0, 0, 0, 1),valign='center',halign='left')
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
            padding=10,
            spacing=10,
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))  # important for scrolling
        
    def on_pre_enter(self):
        self.layout.clear_widgets()
        with sqlite3.connect(DB_PATH) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT job_name from shortlisted WHERE user_id = '{user_id}';")
                self.result = cursor.fetchall()

        

        # Add many labels
        for i in range(len(self.result)):
            lbl = Label(text=f"{self.result[i][0]}", size_hint_y=None, height=40, color=(0, 0, 0, 1))
            self.layout.add_widget(lbl)

        self.scroll.add_widget(self.layout)

        # Add the scroll view to the screen
        self.scroll.scroll_y = 1
        self.add_widget(self.scroll)



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
                        cursor.execute(f"INSERT INTO shortlisted (user_id, job_name) VALUES ('{user_id}', '{self.result[self.index][0]}');")
                        print(user_id)
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
        user_id = self.manager.db_manager.authenticate_user(username, password)
        if user_id:
            self.manager.user_id = user_id
            self.manager.current = "HomeScreen"
        else:
            self.message.text = "Invalid credentials"

class JobCard(FloatLayout):
    def __init__(self, job_data, **kwargs):
        super().__init__(**kwargs)
        self.job_data = job_data
        self.size_hint = (None, None)
        self.size = (340, 500)
        
        # Initialize graphics
        self.setup_graphics()
        
        # Content layout
        content = BoxLayout(orientation='vertical', spacing=8, padding=20,pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        # Job title
        title = Label(text=str(job_data.get('Job_Title', 'N/A')), font_size=18, color=(0.1, 0.1, 0.1, 1),size_hint_y=None, height=50, halign="center", text_size=(300, None), bold=True)
        content.add_widget(title)
        
        # Company
        company = Label(text=str(job_data.get('Company_Name', 'N/A')), font_size=16, color=(0.3, 0.3, 0.3, 1),size_hint_y=None, height=30, halign="center")
        content.add_widget(company)
        
        # Location & Type
        location = job_data.get('Location', 'N/A')
        emp_type = job_data.get('Employment_Type', 'N/A')
        details = Label(text=f"{location} • {emp_type}", font_size=14, color=(0.5, 0.5, 0.5, 1),size_hint_y=None, height=30, halign="center")
        content.add_widget(details)
        
        # Industry tag
        industry = Label(text=f"Industry: {job_data.get('Industry_Tag', 'N/A')}", 
                        font_size=14, color=(0.2, 0.4, 0.8, 1),
                        size_hint_y=None, height=30, halign="center")
        content.add_widget(industry)
        
        # Responsibilities
        resp_title = Label(text="Key Responsibilities:", font_size=14, color=(0.2, 0.2, 0.2, 1),size_hint_y=None, height=25, halign="left", text_size=(300, None))
        content.add_widget(resp_title)
        
        resp_scroll = ScrollView(size_hint=(1, None), height=120)
        resp_text = Label(text=str(job_data.get('Responsibilities', 'N/A')), font_size=12, color=(0.4, 0.4, 0.4, 1),text_size=(300, None), halign="left", valign="top")
        resp_scroll.add_widget(resp_text)
        content.add_widget(resp_scroll)
        
        # Benefits
        benefits_title = Label(text="Benefits:", font_size=14, color=(0.2, 0.2, 0.2, 1),size_hint_y=None, height=25, halign="left", text_size=(300, None))
        content.add_widget(benefits_title)
        
        benefits = Label(text=str(job_data.get('Benefits', 'N/A')), 
                        font_size=12, color=(0.1, 0.6, 0.1, 1),
                        size_hint_y=None, height=50, halign="left", 
                        text_size=(300, None), valign="top")
        content.add_widget(benefits)
        
        # Schedule
        schedule = Label(text=f"Schedule: {job_data.get('Work_Schedule', 'N/A')}", 
                        font_size=12, color=(0.6, 0.4, 0.1, 1),
                        size_hint_y=None, height=30, halign="center")
        content.add_widget(schedule)
        
        self.add_widget(content)
        
        # Track original position for snapping back
        self.original_x = None

    def setup_graphics(self):
        with self.canvas.before:
            Color(0, 0, 0, 1)  # Shadow
            self.shadow = RoundedRectangle(pos=(self.x + 3, self.y - 3), size=self.size, radius=[20])
            Color(1, 1, 1, 1)  # Card background
            self.card_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        if hasattr(self, 'card_bg'):
            self.card_bg.pos = self.pos
            self.card_bg.size = self.size
            self.shadow.pos = (self.x + 3, self.y - 3)
            self.shadow.size = self.size


# --- Main App ---
class CareerMatch(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.db_manager = DatabaseManagement(DB_PATH)
        self.sm.user_id = None
        # Add all screens
        self.sm.add_widget(LoginScreen(name="LoginScreen"))
        self.sm.add_widget(HomeScreen(name="HomeScreen"))
        self.sm.add_widget(AccountScreen(name="AccountScreen"))
        self.sm.add_widget(ShortlistScreen(name="ShortlistScreen"))
        self.sm.add_widget(SwipingScreen(name="SwipingScreen"))
        self.sm.add_widget(ListingScreen(name="ListingScreen"))
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

if __name__ == '__main__':
    CareerMatch().run()
