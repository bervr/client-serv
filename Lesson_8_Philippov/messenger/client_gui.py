"""Программа-клиент"""
import json
from threading import Thread
from common.utils import get_message, send_message
from common.variables import RESPONSE_200
from client import MsgClient
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.app import runTouchApp
from kivy.uix.textinput import TextInput
from functools import partial


class NewClient(MsgClient):

    def hello_user(self, name):
        answer = None
        while answer != RESPONSE_200:
            # user_name = input('Введите свое имя или нажмите Enter чтобы попробовать продолжить анонимно:\n')
            # if user_name == '???':
            #     self.get_clients()
            #     answer = None
            #     continue
            self.add_client_name(name)
            message_to_server = self.create_presence(self.client_name)
            send_message(self.transport, message_to_server)
            # LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
            try:
                answer = self.process_ans(get_message(self.transport))
                # LOGGER.info(f'Получен ответ от сервера {answer}')
            except (ValueError, json.JSONDecodeError):
                print('Не удалось декодировать сообщение сервера.')
                # LOGGER.critical(f'Не удалось декодировать сообщение от сервера')
            else:
                print(f'Вы видны всем под именем {self.client_name}')

    def create_layout(self):
        # добавили основной слой
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        # добавили поле ввода текста
        name_input = TextInput(size_hint_y=None, height=50, multiline=True,
                               hint_text='Введите свое имя или оставьте пустым чтобы продолжить анонимно')
        layout.add_widget(name_input)

        # добавили кнопку отправки
        save_button = Button(text='сохранить и продолжить', size_hint_y=None, height=120)

        save_button.on_press = partial(self.hello_user, name_input.text)
        layout.add_widget(save_button)

        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        root.add_widget(layout)
        runTouchApp(root)

    def start(self):
        self.create_layout()
        self.hello_user()
        receive_thread = Thread(target=self.client_receiving, daemon=True)
        send_thread = Thread(target=self.client_sending, daemon=True)
        receive_thread.start()
        send_thread.start()
        receive_thread.join()
        send_thread.join()


if __name__ == '__main__':
    client = NewClient()
    # client.create_layout()
    client.start()
