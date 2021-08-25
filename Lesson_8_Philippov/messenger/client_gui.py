"""Программа-клиент"""
import json
from threading import Thread
from common.utils import get_message, send_message
from common.variables import RESPONSE_200
from client import MsgClient
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.app import runTouchApp
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label

from functools import partial


class NewClient(MsgClient):
    def callback(self, instace):
        print(f'Нажата кнопка {instace.text}')
        # self.clear_buttons()
        instace.background_color = (0, 1, 0, .85)

    # def clear_buttons(self):
    #     for i in self.contacts:
    #         i.background_color = (0, 1, 1, .85)

    def create_layout(self):
        clients = [123, 456, 789, 987, 654, 321, 505]

        text = 'привет\nи тебе\nкак дела?\nнормально, как сам?\nтоже ничего'

        # добавили основной слой
        # layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        # layout.bind(minimum_height=layout.setter('height'))

        first_box = BoxLayout(spacing=10, padding=10)
        chat_text = Label(text='123456', font_size=40, text_size=(400, 800), size_hint=(.6, 1) )
        self.contacts = GridLayout(cols=1, spacing=10, size_hint=(.4, 1))
        first_box.add_widget(self.contacts)
        first_box.add_widget(chat_text)
        for i in clients:
            self.contacts.add_widget(
                Button(text=f'{i}', on_press=self.callback)
            )

        # добавили поле ввода текста
        # msg_input = TextInput(size_hint_y=None, height=50, multiline=True, hint_text='Напишите здесь что-нибудь')
        # layout.add_widget(msg_input)

        # добавили кнопку отправки
        # send_button = Button(text='отправить!', size_hint_y=None, height=120)
        # # send_button.on_press = partial(self.send)
        # layout.add_widget(send_button)

        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        root.add_widget(first_box)
        runTouchApp(root)

    def start(self):
        self.create_layout()
        # self.hello_user()
        # receive_thread = Thread(target=self.client_receiving, daemon=True)
        # send_thread = Thread(target=self.client_sending, daemon=True)
        # receive_thread.start()
        # send_thread.start()
        # receive_thread.join()
        # send_thread.join()


if __name__ == '__main__':
    client = NewClient()
    client.start()
    # client.create_layout()
