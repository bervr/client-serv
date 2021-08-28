import sys
import time
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from client import MsgClient
import logs.conf.client_log_config
import json
import logging
from common.utils import get_message, send_message
from common.variables import RESPONSE_200, RESPONSE, SENDER, USER, MESSAGE_TEXT, ACCOUNT_NAME, TIME, ACTION, \
    DESTINATION, MESSAGE

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class FirstScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.obj = new_msg

    def get_params(self):
        self.obj.client_name = self.login.text
        self.obj.server_port = self.port.text
        self.obj.server_address = self.server.text
        # print(self.obj.client_name, self.obj.server_address, self.obj.server_port)
        return self.obj


class SecondScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.msg_obj = new_msg
        self.clients = [123, 456, 789, 987, 654, 321, 505, 18, 14, 45]
        # self.clients = []

    def check_name(self):
        print(self.msg_obj.client_name)
        answer = self.msg_obj.hello(self.msg_obj.client_name)
        if answer != RESPONSE_200:
            self.revert()

    def revert(self):
        print('имя уже занято')  # todo  починить надпись о том что имя уже занято
        # self.parent.screens[0].login.text = ''
        # self.parent.screens[0].login.hint_text = f"[color=363636]Нельзя зарегистрироваться под именем  " \
        #                       f"{self.msg_obj.client_name} это имя уже занято[/color]"
        self.manager.current = 'first'

    def render_contacts(self):
        self.update_userlist()
        print(self.msg_obj.remote_users)

        for i in range(len(self.ids.contacts.children)):

            self.ids.contacts.remove_widget(self.ids.contacts.children[-1])

        self.your_name.text = f"[color=000000]Вы видны всем под именем: " \
                              f"{self.msg_obj.client_name if self.msg_obj.client_name else 'Guest'}[/color]"

        if self.clients !=[]:
            for i in self.clients:
                self.contacts.add_widget(
                    Button(text=f'{i}', size_hint_y=None, height=40, on_press=self.select_user)
                )
                # todo scrollview

    def previous_button(self):
        self.manager.current = 'first'

    def select_user(self, instance):
        print(instance.text)
        print(self.msg_obj.client_name)

    def update_userlist(self):
        self.msg_obj.get_clients()


class MyMsg(MsgClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.destination = None
        self.message = ''
        self.to_send = False

    def create_message(self):
        out = {
            DESTINATION: self.destination,
            SENDER: self.client_name,
            ACTION: MESSAGE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.client_name,
                MESSAGE_TEXT: self.message
            }
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {out}')
        return out

    def client_receiving(self):
        while True:
            try:
                answer = get_message(self.transport)
                print(answer)
                if RESPONSE in answer:
                    self.process_ans(answer)
                    print(self.remote_users)
                else:
                    print(f'\nUser {answer[SENDER]} sent: {answer[USER][MESSAGE_TEXT]}')
                    LOGGER.info(f'Сообщение из чята от {answer[SENDER]}: {answer[USER][MESSAGE_TEXT]}')
                    # print(f'Сообщение из чята от {answer["sender"]}: {answer["message_text"]}')
            except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                sys.exit(1)

    def client_sending(self):
        LOGGER.info('Режим работы - отправка сообщений')
        while True:
            if self.to_send:
                try:
                    send_message(self.transport, self.create_message())
                    self.to_send = False
                except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
                    LOGGER.error(f'Соединение с сервером {self.server_address} было утеряно')
                    sys.exit(1)

class ClientApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # new_msg.start_threads()


    def build(self):
        # Добавляю красивый переход FadeTransition
        sm = ScreenManager(transition=FadeTransition())  # Создаю менеджер экранов sm
        # обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        # в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        new_msg = MyMsg()
        # new_msg = MsgClient()
        first_screen = FirstScreen(new_msg, name='first')
        second_screen = SecondScreen(new_msg, name='second')
        sm.add_widget(first_screen)
        sm.add_widget(second_screen)
        # new_msg.start_threads()
        return sm


if __name__ == "__main__":
    ClientApp().run()
    # ClientApp().new_msg.start_threads()