from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

Builder.load_string('''
<FirstScreen>:
    BoxLayout:
        canvas:
            Color:
                rgba:(1,1,1,1)
            Rectangle:
                pos:self.pos
                size:self.size
        orientation:'vertical'
        BoxLayout:
            size_hint:(1,0.8)
            Label:
                text:'This is first screen'
                color:(0,0,0,1)
            Label:
                text:'Push button "next"'
                color:(0,0,0,1)
        Button:
            text:'Next'
            size_hint:(1,0.2)
            on_press:root.manager.current='second'


<SecondScreen>:
    BoxLayout:
        canvas:
            Color:
                rgba:(0,0,0,1)
            Rectangle:
                pos:self.pos
                size:self.size
        orientation:'vertical'
        BoxLayout:
            size_hint:(1,0.8)
            Label:
                text:'This is second screen'
            Label:
                text:'Push button "previous"'
        Button:
            text:'Previous'
            size_hint:(1,0.2)
            on_press:root.previous_button()

''')


class FirstScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)


class SecondScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

    def previous_button(self):
        self.manager.current='first'


class TestApp(App):
    def build(self):
        #Добавляю красивый переход FadeTransition
        sm=ScreenManager(transition=FadeTransition())#Создаю менеджер экранов sm
        #обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        #в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        sm.add_widget(FirstScreen(name='first'))
        sm.add_widget(SecondScreen(name='second'))
        return sm

if __name__=="__main__":
    TestApp().run()