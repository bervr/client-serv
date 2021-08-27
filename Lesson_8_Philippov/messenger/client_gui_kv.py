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
from common.variables import RESPONSE_200

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


        on_pre_enter: (self.render_contacts())

    def hello_user(self):
        answer = None
        if answer != RESPONSE_200:
            self.obj.add_client_name(self.obj.client_name)
            message_to_server = self.obj.create_presence(self.obj.client_name)
            send_message(self.obj.transport, message_to_server)
            LOGGER.info(f'Отправка сообщения на сервер - {message_to_server}')
            try:
                answer = self.obj.process_ans(get_message(self.obj.transport))
                LOGGER.info(f'Получен ответ от сервера {answer}')
            except (ValueError, json.JSONDecodeError):
                # print('Не удалось декодировать сообщение сервера.')
                LOGGER.critical(f'Не удалось декодировать сообщение от сервера')
            else:
                print(f'Вы видны всем под именем {self.obj.client_name}')
        else:
            self.app.first_screen.login.text = 'fail'
            self.manager.current = 'first'

    def revert(self):
        self.parent.screens[0].login.text = 'fail'
        self.manager.current = 'first'





    def render_contacts(self):
        for i in range(len(self.ids.contacts.children)):

            self.ids.contacts.remove_widget(self.ids.contacts.children[-1])

        self.your_name.text = f"[color=000000]Вы видны всем под именем: " \
                              f"{self.msg_obj.client_name if self.msg_obj.client_name else 'Guest'}[/color]"
        # self.contacts.add_widget(
        #     Button(text='ALL', on_press=self.select_user)
        # )
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
        pass



class ClientApp(App):
    def build(self):
        # Добавляю красивый переход FadeTransition
        sm = ScreenManager(transition=FadeTransition())  # Создаю менеджер экранов sm
        # обязательно нужно дать имя экрану, ведь по этому имени и будет производиться переключение
        # в kv файле для преключения нужно использовать root.manager.current, а в коде self.manager.current
        new_msg = MsgClient()
        first_screen = FirstScreen(new_msg, name='first')
        second_screen = SecondScreen(new_msg, name='second')
        sm.add_widget(first_screen)
        sm.add_widget(second_screen)
        return sm


if __name__ == "__main__":
    ClientApp().run()
