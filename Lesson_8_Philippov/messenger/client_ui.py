"""Программа-клиент"""
from client import MsgClient
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.app import runTouchApp
from kivy.uix.textinput import TextInput
from functools import partial

class NewClient(MsgClient):

    def create_layout(self):
        # добавили основной слой
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        #добавили поле ввода текста
        msg_input = TextInput(size_hint_y=None, height=50, multiline=True, hint_text='Напишите здесь что-нибудь')
        layout.add_widget(msg_input)

        #добавили кнопку отправки
        send_button = Button(text='отправить!', size_hint_y=None, height=120)
        # send_button.on_press = partial(self.send)
        layout.add_widget(send_button)

        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        runTouchApp(root)





if __name__ == '__main__':
    client = NewClient()
    client.start()
    client.create_layout()
