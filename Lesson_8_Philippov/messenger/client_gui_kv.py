from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.button import Button
from client import MsgClient
import logs.conf.client_log_config
import logging

LOGGER = logging.getLogger('client')  # забрали логгер из конфига


class FirstScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.obj = new_msg

    def hello_user(self):
        # super().__init__(**kwargs)
        self.obj.client_name = self.login.text
        self.obj.server_port = self.port.text
        self.obj.server_address = self.server.text
        # print(self.login.text, self.login.text)
        print(self.obj.client_name, self.obj.server_address, self.obj.server_port)
        # user_name = self.client_name
        # return self.hello_user()
        # print(self.client_name, 'hello user')
        # self.get_start_params()
        return self.obj

    def o_two(self):
        self.hello_user()
        self.manager.current = 'second'


class SecondScreen(Screen):
    def __init__(self, new_msg, **kwargs):
        super().__init__(**kwargs)
        self.msg_obj = new_msg
        self.clients = [123, 456, 789, 987, 654, 321, 505]
        self.render_contacts()
        # print(self.msg_obj.client_name)
        # print(MsgClient().client_name)
        # self.contacts.add_widget(Button(text='all', on_press=self.select_user))

    def render_contacts(self):
        for i in range(len(self.ids.contacts.children)):
            self.ids.contacts.remove_widget(self.ids.contacts.children[-1])

        self.your_name.text = f"[color=000000]Вы видны всем под именем: " \
                              f"{self.msg_obj.client_name if self.msg_obj.client_name else 'Guest'}[/color]"
        # self.contacts.add_widget(
        #     Button(text='ALL', on_press=self.select_user)
        # )

        for i in self.clients:
            self.contacts.add_widget(
                Button(text=f'{i}', on_press=self.select_user)
            )

    def previous_button(self):
        self.manager.current = 'first'

    def select_user(self, instance):
        # self.manager.current = 'third'
        print(instance.text)
        print(self.msg_obj.client_name)


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
    # Compare().run()
