from kivy.config import Config

# Force window size
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '700')
Config.set('graphics', 'resizable', False)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label


# Home screen
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # discover
        discoverScroll = ScrollView(
            size_hint=(None, None),
            size_hint_y=None,
            size=(700, 300),
            pos=(50, 850)
        )

        discoverLayout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            padding=10,
            spacing=10,
        )
        discoverLayout.bind(minimum_width=discoverLayout.setter('width'))

        #temp
        for i in range(50):
            lbl = Label(text=f"Item {i+1}", size_hint_x=None, height=40, color=(0, 0, 0, 1))
            discoverLayout.add_widget(lbl)

        discoverScroll.add_widget(discoverLayout)

        # Add the scroll view to the screen
        discoverScroll.scroll_x = 0
        self.add_widget(discoverScroll)

        shortlistScroll = ScrollView(
            size_hint=(None, None),
            size_hint_y=None,
            size=(700, 450),
            pos=(50, 200)
        )

        shortlistLayout = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            padding=10,
            spacing=10,
        )
        shortlistLayout.bind(minimum_width=shortlistLayout.setter('width'))  # important for scrolling

        # Add many labels
        for i in range(50):
            lbl = Label(text=f"Item {i+1}", size_hint_x=None, height=40, color=(0, 0, 0, 1))
            shortlistLayout.add_widget(lbl)

        shortlistScroll .add_widget(shortlistLayout)

        # Add the scroll view to the screen
        shortlistScroll.scroll_x = 0
        self.add_widget(shortlistScroll)

# Define Screen 2
class AccountScreen(Screen):
    def toHome(self):
        self.manager.current = "HomeScreen"

class ShortlistScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView
        scroll = ScrollView(
            size_hint=(None, None),
            size_hint_y=None,
            size=(700, 1025),
            pos=(50, 175)
        )

        # Layout inside the scroll view
        layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=10,
            spacing=10,
        )
        layout.bind(minimum_height=layout.setter('height'))  # important for scrolling

        # Add many labels
        for i in range(50):
            lbl = Label(text=f"Item {i+1}", size_hint_y=None, height=40, color=(0, 0, 0, 1))
            layout.add_widget(lbl)

        scroll.add_widget(layout)

        # Add the scroll view to the screen
        scroll.scroll_y = 1
        self.add_widget(scroll)

class SwipingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_x = 0
        self.start_y = 0

        with self.canvas:
            Color(0,0,0,1)
            self.card = Rectangle(pos=(50, 200), size=(700, 1000))
        

    def on_touch_down(self, touch):
        self.start_x = touch.x
        self.start_y = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        dx = touch.x - self.start_x
        dy = touch.y - self.start_y

        if abs(dx) > abs(dy):
            if dx > 50:
                print("Swipe Right")
            elif dx < -50:
                print("Swipe Left")


class ListingScreen(Screen):
    def toHome(self):
        self.manager.current = "HomeScreen"

# Main App
class CareerMatch(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())  # adds a fade effect when switching
        self.sm.add_widget(HomeScreen(name="HomeScreen"))
        self.sm.add_widget(AccountScreen(name="AccountScreen"))
        self.sm.add_widget(ShortlistScreen(name="ShortlistScreen"))
        self.sm.add_widget(SwipingScreen(name="SwipingScreen"))
        self.sm.add_widget(ListingScreen(name="ListingScreen"))
        return self.sm

    def toHome(self):
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

