from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

from kivy.graphics import Color, RoundedRectangle, PushMatrix, PopMatrix, Translate, Rotate
from kivy.animation import Animation
from kivy.clock import Clock
import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")

class DatabaseManagement:
    def __init__(self, db_path):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                
                # Create/update users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        full_name TEXT,
                        email TEXT,
                        phone TEXT
                    )
                ''')
                
                # Create shortlist table (drop and recreate to fix schema)
                cursor.execute("DROP TABLE IF EXISTS shortlist")
                cursor.execute('''
                    CREATE TABLE shortlist (
                        user_id INTEGER,
                        job_rowid INTEGER,
                        UNIQUE(user_id, job_rowid),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                db.commit()
                print("Database setup completed successfully")
        except Exception as e:
            print(f"Database setup error: {e}")

    def create_user(self, username, password):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(f"INSERT INTO users (username, password) VALUES ({username}, {password})")
                db.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def authenticate_user(self, username, password):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()
                cursor.execute(f"SELECT id FROM users WHERE username='{username}' AND password=='{password}'")
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    def get_all_jobs(self):
        try:
            with sqlite3.connect(self.db_path) as db:
                df = pd.read_sql_query("SELECT ROWID, * FROM listings", db)
            print(f"Retrieved {len(df)} jobs from database")
            return df
        except Exception as e:
            print(f"Error getting jobs: {e}")
            return pd.DataFrame()

    def matched_jobs(self, user_interests, jobs_df):
        with sqlite3.connect(self.db_path) as db:

            cursor = db.cursor()

            queryString = f"select * from listings where Industry_Tag == '{user_interests[0]}'"

            if len(user_interests) > 1:
                for i in range(1, len(user_interests)-1):
                    queryString += f" or Industry_Tag == '{user_interests[i]}'"
            queryString += ';'

            result = cursor.execute(queryString)
            #result = cursor.execute("SELECT * from listings;")
            imported = [b for b in result.fetchall()] #0: the number of arguments returned.

            return pd.DataFrame(imported)

    def add_to_shortlist(self, user_id, job_name):
        try:
            with sqlite3.connect(self.db_path) as db:
                cursor = db.cursor()

                print(f"=== SHORTLIST DEBUG ===")
                print(f"Adding to shortlist: user_id={user_id} job={job_name}")

                # Check if already in shortlist
                cursor.execute("SELECT COUNT(*) FROM shortlisted WHERE user_id=? AND job_name=?", (user_id, job_name))
                already_exists = cursor.fetchone()[0]
                print(f"Already in shortlist: {already_exists > 0}")
                
                if already_exists > 0:
                    print("Job already in shortlist")
                    return True
                
                # Insert into shortlist
                cursor.execute("INSERT INTO shortlisted (user_id, job_name) VALUES (?, ?)", (user_id, job_name))
                rows_affected = cursor.rowcount
                print(f"Rows affected by insert: {rows_affected}")
                
                db.commit()
                print("Transaction committed")
                
                # Verify insertion
                cursor.execute("SELECT COUNT(*) FROM shortlisted WHERE user_id=? AND job_name=?", (user_id, job_name))
                final_count = cursor.fetchall()
                print(f"Final verification count: {final_count}")
                
                if final_count > 0:
                    print("SUCCESS: Job successfully added to shortlist")
                    return True
                else:
                    print("ERROR: Job was not added to shortlist")
                    return False
                    
        except Exception as e:
            print(f"ERROR adding to shortlist: {e}")
            return False

    def get_shortlist(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as db:
                df = pd.read_sql_query('''
                    SELECT l.ROWID, l.* FROM listings l
                    JOIN shortlist s ON l.ROWID = s.job_rowid
                    WHERE s.user_id = ?
                ''', db, params=(user_id,))
                print(f"Retrieved {len(df)} shortlisted jobs for user {user_id}")
                return df
        except Exception as e:
            print(f"Database error getting shortlist: {e}")
            return pd.DataFrame()


class ModernCard(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class LoginScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        
        # Background
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        
        # Title
        title = Label(text="CareerMatch", font_size=32, color=(1, 1, 1, 1), 
                     size_hint_y=None, height=80)
        main_layout.add_widget(title)
        
        # Login form
        form_layout = BoxLayout(orientation='vertical', spacing=15, 
                               size_hint_y=None, height=200)
        
        self.username_input = TextInput(hint_text="Username", multiline=False, 
                                       size_hint_y=None, height=45)
        self.password_input = TextInput(hint_text="Password", password=True, 
                                       multiline=False, size_hint_y=None, height=45)
        
        login_btn = Button(text="Login", size_hint_y=None, height=50, 
                          background_color=(0.2, 0.6, 1, 1), on_press=self.login)
        signup_btn = Button(text="Sign Up", size_hint_y=None, height=50,
                           background_color=(0.6, 0.2, 1, 1), on_press=self.go_signup)
        
        form_layout.add_widget(self.username_input)
        form_layout.add_widget(self.password_input)
        form_layout.add_widget(login_btn)
        form_layout.add_widget(signup_btn)
        
        main_layout.add_widget(form_layout)
        
        # Message
        self.message = Label(text="", color=(1, 0.3, 0.3, 1), size_hint_y=None, height=40)
        main_layout.add_widget(self.message)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def login(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.message.text = "Please enter both username and password"
            return
            
        user_id = self.db_manager.authenticate_user(username, password)
        if user_id:
            self.manager.user_id = user_id
            self.manager.username = username
            self.manager.current = "InterestScreen"
            self.username_input.text = ""
            self.password_input.text = ""
            self.message.text = ""
        else:
            self.message.text = "Invalid username or password"

    def go_signup(self, instance):
        self.manager.current = "SignupScreen"


class SignupScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        
        # Background
        with self.canvas.before:
            Color(0.1, 0.1, 0.2, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=40)
        
        # Title
        title = Label(text="Create Account", font_size=24, color=(1, 1, 1, 1),
                     size_hint_y=None, height=60)
        main_layout.add_widget(title)
        
        # Form
        form_layout = BoxLayout(orientation='vertical', spacing=15)
        
        self.username_input = TextInput(hint_text="Username", multiline=False,
                                       size_hint_y=None, height=45)
        self.password_input = TextInput(hint_text="Password", password=True,
                                       multiline=False, size_hint_y=None, height=45)
        
        signup_btn = Button(text="Sign Up", size_hint_y=None, height=50,
                           background_color=(0.2, 0.8, 0.2, 1), on_press=self.signup)
        back_btn = Button(text="Back to Login", size_hint_y=None, height=50,
                         background_color=(0.6, 0.6, 0.6, 1), on_press=self.go_login)
        
        form_layout.add_widget(self.username_input)
        form_layout.add_widget(self.password_input)
        form_layout.add_widget(signup_btn)
        form_layout.add_widget(back_btn)
        
        main_layout.add_widget(form_layout)
        
        self.message = Label(text="", color=(1, 0.3, 0.3, 1), size_hint_y=None, height=40)
        main_layout.add_widget(self.message)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def signup(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        
        if not username or not password:
            self.message.text = "Please enter both username and password"
            return
        
        if len(username) < 3:
            self.message.text = "Username must be at least 3 characters"
            return
            
        if len(password) < 4:
            self.message.text = "Password must be at least 4 characters"
            return
            
        if self.db_manager.create_user(username, password):
            self.message.text = "Account created! Redirecting..."
            self.username_input.text = ""
            self.password_input.text = ""
            Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'LoginScreen'), 1.5)
        else:
            self.message.text = "Username already exists"

    def go_login(self, instance):
        self.manager.current = "LoginScreen"


class InterestScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        
        # Background
        with self.canvas.before:
            Color(0.05, 0.05, 0.15, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        
        # Header
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        logout_btn = Button(text="Logout", size_hint_x=None, width=80,
                           background_color=(0.8, 0.3, 0.3, 1), on_press=self.logout)
        title = Label(text="Find Your Dream Job", font_size=20, color=(1, 1, 1, 1))
        shortlist_btn = Button(text="Shortlist", size_hint_x=None, width=80,
                              background_color=(0.3, 0.7, 0.3, 1), on_press=self.go_shortlist)
        
        header_layout.add_widget(logout_btn)
        header_layout.add_widget(title)
        header_layout.add_widget(shortlist_btn)
        main_layout.add_widget(header_layout)
        
        # Instructions
        instructions = Label(text="Enter your job interests separated by commas\n(e.g., IT, Marketing, Design, Sales, Engineering)", 
                           color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=80)
        main_layout.add_widget(instructions)
        
        # Interest input
        self.interest_input = TextInput(hint_text="Your interests...", multiline=True,
                                       size_hint_y=None, height=120)
        main_layout.add_widget(self.interest_input)
        
        # Search button
        search_btn = Button(text="Find Matching Jobs", size_hint_y=None, height=60,
                           background_color=(1, 0.5, 0, 1), font_size=18, on_press=self.search_jobs)
        main_layout.add_widget(search_btn)
        
        # Message
        self.message = Label(text="", color=(1, 0.8, 0, 1), size_hint_y=None, height=60)
        main_layout.add_widget(self.message)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def search_jobs(self, instance):
        interests_text = self.interest_input.text.strip()
        if not interests_text:
            self.message.text = "Please enter your interests"
            return
            
        user_interests = [i.strip() for i in interests_text.split(",") if i.strip()]
        print(f"User interests: {user_interests}")
        
        self.message.text = "Searching for jobs..."
        
        all_jobs = self.db_manager.get_all_jobs()
        print(f"Total jobs found: {len(all_jobs)}")
        
        if all_jobs.empty:
            self.message.text = "No jobs found in database.\nPlease check if listings.db exists."
            return
            
        matched_jobs = self.db_manager.matched_jobs(user_interests, all_jobs)
        print(f"Matched jobs: {len(matched_jobs)}")
        
        if matched_jobs.empty:
            self.message.text = f"No jobs match '{interests_text}'.\nTry terms like: IT, Marketing, Sales, Finance, Engineering, Healthcare, Developer, Manager, Analyst"
        else:
            self.message.text = f"Found {len(matched_jobs)} matching jobs!\nRedirecting to swipe..."
            # Store the matched jobs and interests for debugging
            self.last_search_interests = user_interests
            self.last_matched_count = len(matched_jobs)
            Clock.schedule_once(lambda dt: self.go_to_swiping(matched_jobs), 1.5)

    def go_to_swiping(self, matched_jobs):
        swiping_screen = self.manager.get_screen("SwipingScreen")
        swiping_screen.load_jobs(matched_jobs)
        self.manager.current = "SwipingScreen"

    def go_shortlist(self, instance):
        self.manager.current = "ShortlistScreen"

    def logout(self, instance):
        self.manager.user_id = None
        self.manager.username = None
        self.interest_input.text = ""
        self.message.text = ""
        self.manager.current = "LoginScreen"


class JobCard(FloatLayout):
    def __init__(self, job_data, **kwargs):
        super().__init__(**kwargs)
        self.job_data = job_data
        self.size_hint = (None, None)
        self.size = (340, 500)
        
        # Initialize graphics
        self.setup_graphics()
        
        # Content layout
        content = BoxLayout(orientation='vertical', spacing=8, padding=20,
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        # Job title
        title = Label(text=str(job_data.get('Job_Title', 'N/A')), 
                     font_size=18, color=(0.1, 0.1, 0.1, 1),
                     size_hint_y=None, height=50, halign="center", 
                     text_size=(300, None), bold=True)
        content.add_widget(title)
        
        # Company
        company = Label(text=str(job_data.get('Company_Name', 'N/A')), 
                       font_size=16, color=(0.3, 0.3, 0.3, 1),
                       size_hint_y=None, height=30, halign="center")
        content.add_widget(company)
        
        # Location & Type
        location = job_data.get('Location', 'N/A')
        emp_type = job_data.get('Employment_Type', 'N/A')
        details = Label(text=f"{location} • {emp_type}", 
                       font_size=14, color=(0.5, 0.5, 0.5, 1),
                       size_hint_y=None, height=30, halign="center")
        content.add_widget(details)
        
        # Industry tag
        industry = Label(text=f"Industry: {job_data.get('Industry_Tag', 'N/A')}", 
                        font_size=14, color=(0.2, 0.4, 0.8, 1),
                        size_hint_y=None, height=30, halign="center")
        content.add_widget(industry)
        
        # Responsibilities
        resp_title = Label(text="Key Responsibilities:", font_size=14, color=(0.2, 0.2, 0.2, 1),
                          size_hint_y=None, height=25, halign="left", text_size=(300, None))
        content.add_widget(resp_title)
        
        resp_scroll = ScrollView(size_hint=(1, None), height=120)
        resp_text = Label(text=str(job_data.get('Responsibilities', 'N/A')), 
                         font_size=12, color=(0.4, 0.4, 0.4, 1),
                         text_size=(300, None), halign="left", valign="top")
        resp_scroll.add_widget(resp_text)
        content.add_widget(resp_scroll)
        
        # Benefits
        benefits_title = Label(text="Benefits:", font_size=14, color=(0.2, 0.2, 0.2, 1),
                              size_hint_y=None, height=25, halign="left", text_size=(300, None))
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
            Color(0, 0, 0, 0.1)  # Shadow
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


class SwipingScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.jobs = pd.DataFrame()
        self.current_index = 0
        self.current_card = None
        self.touch_start_x = None
        self.original_card_x = None
        
        # Background
        with self.canvas.before:
            Color(0.95, 0.95, 0.98, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text="< Back", size_hint_x=None, width=80,
                         background_color=(0.6, 0.6, 0.6, 1), on_press=self.go_back)
        title = Label(text="Swipe to Match", font_size=18, color=(0.2, 0.2, 0.2, 1))
        shortlist_btn = Button(text="Shortlist", size_hint_x=None, width=80,
                              background_color=(0.3, 0.7, 0.3, 1), on_press=self.go_shortlist)
        
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(shortlist_btn)
        main_layout.add_widget(header)
        
        # Card container
        self.card_container = FloatLayout(size_hint=(1, 1))
        main_layout.add_widget(self.card_container)
        
        # Instructions
        instructions = Label(text="< Swipe left to skip  •  Swipe right to like >", 
                           color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=30)
        main_layout.add_widget(instructions)
        
        # Action buttons
        button_layout = BoxLayout(orientation='horizontal', spacing=20, 
                                 size_hint_y=None, height=60, padding=[40, 0])
        
        skip_btn = Button(text="X Skip", size_hint_x=0.45,
                         background_color=(1, 0.3, 0.3, 1), on_press=self.skip_job,
                         font_size=16)
        like_btn = Button(text="Like", size_hint_x=0.45,
                         background_color=(0.3, 0.8, 0.3, 1), on_press=self.like_job,
                         font_size=16)
        
        button_layout.add_widget(skip_btn)
        button_layout.add_widget(like_btn)
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def load_jobs(self, jobs_df):
        self.jobs = jobs_df.reset_index(drop=True)
        self.current_index = 0
        print(f"Loaded {len(self.jobs)} jobs for swiping")
        self.show_current_job()

    def show_current_job(self):
        self.card_container.clear_widgets()
        
        if self.current_index >= len(self.jobs):
            # No more jobs
            no_jobs = Label(text="No more jobs!\n\nGo back to search again\nor check your shortlist", font_size=18, color=(0.3, 0.3, 0.3, 1), halign="center")
            self.card_container.add_widget(no_jobs)
            return
        
        job = self.jobs.iloc[self.current_index]
        self.current_card = JobCard(job)
        self.current_card.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        # Store original position
        Clock.schedule_once(lambda dt: setattr(self, 'original_card_x', self.current_card.x), 0.1)
        self.card_container.add_widget(self.current_card)

    def skip_job(self, instance):
        if self.current_card:
            print("Skipping job...")
            # Animate card sliding left
            anim = Animation(x=-400, duration=0.3)
            anim.bind(on_complete=lambda *args: self.next_job())
            anim.start(self.current_card)

    def like_job(self, instance):
        if self.current_card and self.current_index < len(self.jobs):
            job = self.jobs.iloc[self.current_index]
            print(job)
            
            print(f"=== LIKE JOB DEBUG ===")
            print(f"Job Title: {job.get('Job_Title', 'Unknown')}")
            print(f"User ID: {self.manager.user_id}")
            print(f"User ID type: {type(self.manager.user_id)}")

            jobName = job.get('Job_Title')
            
            if self.manager.user_id is not None:
                # Ensure both are integers
                try:
                    user_id_int = int(self.manager.user_id)
                    print(f"Converting to: user_id={user_id_int}")
                    
                    success = self.db_manager.add_to_shortlist(user_id_int, jobName)
                    if success:
                        print("SUCCESS: Added to shortlist!")
                        # Show visual feedback
                        Clock.schedule_once(lambda dt: self.show_like_feedback(), 0)
                    else:
                        print("FAILED: Could not add to shortlist")
                except (ValueError, TypeError) as e:
                    print(f"CONVERSION ERROR: {e}")
            else:
                print("ERROR: Missing job_rowid or user_id")
                print(f"user_id is None: {self.manager.user_id is None}")
            
            # Animate card sliding right
            anim = Animation(x=800, duration=0.3)
            anim.bind(on_complete=lambda *args: self.next_job())
            anim.start(self.current_card)
    
    def show_like_feedback(self):
        # Brief visual feedback that job was liked
        pass

    def next_job(self):
        self.current_index += 1
        Clock.schedule_once(lambda dt: self.show_current_job(), 0.1)

    def on_touch_down(self, touch):
        if self.current_card and self.current_card.collide_point(*touch.pos):
            self.touch_start_x = touch.x
            self.original_card_x = self.current_card.x
            print(f"Touch started at {touch.x}, card at {self.current_card.x}")
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if (hasattr(self, 'touch_start_x') and self.touch_start_x is not None 
            and self.current_card and hasattr(self, 'original_card_x')):
            
            dx = touch.x - self.touch_start_x
            new_x = self.original_card_x + dx
            self.current_card.x = new_x
            
            # Add visual feedback
            opacity = max(0.7, 1 - abs(dx) / 200)
            
            # Update card graphics with tilt effect
            rotation = dx / 10  # Rotation based on swipe distance
            self.current_card.canvas.before.clear()
            with self.current_card.canvas.before:
                PushMatrix()
                Translate(self.current_card.center_x, self.current_card.center_y)
                Rotate(angle=rotation)
                Translate(-self.current_card.center_x, -self.current_card.center_y)
                Color(0, 0, 0, 0.1)  # Shadow
                RoundedRectangle(pos=(self.current_card.x + 3, self.current_card.y - 3), 
                               size=self.current_card.size, radius=[20])
                Color(1, 1, 1, opacity)  # Card background with opacity
                RoundedRectangle(pos=self.current_card.pos, size=self.current_card.size, radius=[20])
                PopMatrix()
            
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if (hasattr(self, 'touch_start_x') and self.touch_start_x is not None 
            and self.current_card and hasattr(self, 'original_card_x')):
            
            dx = touch.x - self.touch_start_x
            print(f"Touch ended, dx: {dx}")
            
            # Reset touch tracking
            self.touch_start_x = None
            
            if abs(dx) > 80:  # Swipe threshold (reduced for easier swiping)
                if dx > 0:  # Right swipe (like)
                    print("Right swipe detected - liking job")
                    self.like_job(None)
                else:  # Left swipe (skip)
                    print("Left swipe detected - skipping job")
                    self.skip_job(None)
            else:
                # Snap back to center
                print("Snapping back to center")
                anim = Animation(x=self.original_card_x, duration=0.3)
                anim.bind(on_complete=lambda *args: self.reset_card_graphics())
                anim.start(self.current_card)
            return True
        return super().on_touch_up(touch)

    def reset_card_graphics(self):
        if self.current_card:
            self.current_card.setup_graphics()

    def go_back(self, instance):
        self.manager.current = "InterestScreen"

    def go_shortlist(self, instance):
        self.manager.current = "ShortlistScreen"


class ShortlistScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        
        # Background
        with self.canvas.before:
            Color(0.05, 0.1, 0.05, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        main_layout = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = Button(text="< Back", size_hint_x=None, width=80,
                         background_color=(0.6, 0.6, 0.6, 1), on_press=self.go_back)
        title = Label(text="Your Shortlist", font_size=20, color=(1, 1, 1, 1))
        refresh_btn = Button(text="Refresh", size_hint_x=None, width=80,
                           background_color=(0.3, 0.6, 0.8, 1), on_press=self.refresh_shortlist)
        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(refresh_btn)
        main_layout.add_widget(header)
        
        # Scrollable job list
        self.scroll = ScrollView()
        self.layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=10)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.scroll.add_widget(self.layout)
        main_layout.add_widget(self.scroll)
        
        self.add_widget(main_layout)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def on_enter(self):
        self.load_shortlist()

    def load_shortlist(self):
        if not hasattr(self.manager, 'user_id') or not self.manager.user_id:
            return
            
        jobs = self.db_manager.get_shortlist(self.manager.user_id)
        self.layout.clear_widgets()
        
        if jobs.empty:
            empty_msg = Label(text="No shortlisted jobs yet!\n\nSwipe right on jobs to add them here.", 
                             color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=100,
                             halign="center", font_size=16)
            self.layout.add_widget(empty_msg)
        else:
            for _, job in jobs.iterrows():
                # Create job card with background
                job_card = FloatLayout(size_hint_y=None, height=140)
                
                # Content
                content = BoxLayout(orientation='vertical', padding=15, spacing=5)
                
                title_label = Label(text=f"Job: {job.get('Job_Title', 'N/A')}", 
                                  font_size=16, color=(0.1, 0.1, 0.1, 1),
                                  size_hint_y=None, height=30, halign="left", 
                                  text_size=(320, None), bold=True)
                
                company_label = Label(text=f"Company: {job.get('Company_Name', 'N/A')}", 
                                     font_size=14, color=(0.3, 0.3, 0.3, 1),
                                     size_hint_y=None, height=25, halign="left", 
                                     text_size=(320, None))
                
                location_text = job.get('Location', 'N/A')
                emp_type_text = job.get('Employment_Type', 'N/A')
                details_label = Label(text=f"Location: {location_text} | Type: {emp_type_text}", 
                                    font_size=12, color=(0.5, 0.5, 0.5, 1),
                                    size_hint_y=None, height=25, halign="left", 
                                    text_size=(320, None))
                
                benefits_text = str(job.get('Benefits', 'N/A'))
                if len(benefits_text) > 60:
                    benefits_text = benefits_text[:60] + "..."
                benefits_label = Label(text=f"Benefits: {benefits_text}", 
                                     font_size=12, color=(0.1, 0.6, 0.1, 1),
                                     size_hint_y=None, height=35, halign="left", 
                                     text_size=(320, None))
                
                industry_label = Label(text=f"Industry: {job.get('Industry_Tag', 'N/A')}", 
                                     font_size=12, color=(0.2, 0.4, 0.8, 1),
                                     size_hint_y=None, height=25, halign="left", 
                                     text_size=(320, None))
                
                content.add_widget(title_label)
                content.add_widget(company_label)
                content.add_widget(details_label)
                content.add_widget(benefits_label)
                content.add_widget(industry_label)
                
                job_card.add_widget(content)
                
                # Update background when card position changes
                def update_card_bg(card, *args):
                    card.canvas.before.clear()
                    with card.canvas.before:
                        Color(1, 1, 1, 0.95)
                        RoundedRectangle(pos=card.pos, size=card.size, radius=[10])
                
                job_card.bind(pos=update_card_bg, size=update_card_bg)
                update_card_bg(job_card)  # Initial setup
                
                self.layout.add_widget(job_card)

    def refresh_shortlist(self, instance):
        self.load_shortlist()

    def go_back(self, instance):
        self.manager.current = "InterestScreen"


class CareerMatchApp(App):
    def build(self):
        self.title = "CareerMatch"
        
        # Initialize database
        try:
            self.db_manager = DatabaseManagement(DB_PATH)
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return Label(text=f"Database Error: {e}")
        
        # Create screen manager
        sm = ScreenManager(transition=SlideTransition())
        sm.user_id = None
        sm.username = None
        
        # Add all screens
        try:
            sm.add_widget(LoginScreen(self.db_manager, name="LoginScreen"))
            sm.add_widget(SignupScreen(self.db_manager, name="SignupScreen"))
            sm.add_widget(InterestScreen(self.db_manager, name="InterestScreen"))
            sm.add_widget(SwipingScreen(self.db_manager, name="SwipingScreen"))
            sm.add_widget(ShortlistScreen(self.db_manager, name="ShortlistScreen"))
            print("All screens added successfully")
        except Exception as e:
            print(f"Error adding screens: {e}")
            return Label(text=f"Screen Error: {e}")
        
        return sm


if __name__ == '__main__':
    print("Starting CareerMatch App...")
    try:
        CareerMatchApp().run()
    except Exception as e:
        print(f"App startup error: {e}")