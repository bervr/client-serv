from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, BINARY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


class ServerStorage:
    """Класс хранилища сервера"""

    class Users(Base):
        """Таблица пользователя"""
        __tablename__ = 'Users'
        id = Column(Integer, primary_key=True)
        login = Column(String, unique=True)
        info = Column(String)
        last_login = Column(DateTime)
        pubkey = Column(Text)
        passwd_hash = Column(String)

        def __init__(self, login, passwd_hash, info=''):
            self.login = login
            self.info = info
            self.last_login = None
            self.pubkey = None
            self.passwd_hash = passwd_hash

        def __repl__(self):
            return f'User{self.id}({self.login})'

    class UserLoginHistory(Base):
        """Таблица истории входов"""
        __tablename__ = 'user_login_history'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'))
        ipaddress = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ipaddress, port, login_time):
            self.user_id = user_id
            self.ipaddress = ipaddress
            self.port = port
            self.login_time = login_time

        def __repl__(self):
            return f'User{self.user_id}-ip{self.ipaddress}:{self:port}-{self.login_time}'

    class UsersHistory(Base):
        """Таблица счетчик отправленых и полученых сообщений"""
        __tablename__ = 'history'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('Users.id'))
        sent = Column(Integer)
        accepted = Column(Integer)

        def __init__(self, user):
            self.user = user
            self.sent = 0
            self.accepted = 0

    class ActiveUsers(Base):
        """Таблица подключеных пользователей"""
        __tablename__ = 'active_users'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'), unique=True)
        ipaddress = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ipaddress, port, login_time):
            self.user_id = user_id
            self.ipaddress = ipaddress
            self.port = port
            self.login_time = login_time

        def __repl__(self):
            return f'User{self.user_id}-ip{self.ipaddress}:{self:port}-{self.login_time}'

    class Contacts(Base):
        """Таблица контактов"""
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        user_id = Column(ForeignKey('Users.id'))
        contact_id = Column(ForeignKey('Users.id'))

        def __init__(self, user_id, contact_id):
            self.user_id = user_id
            self.contact_id = contact_id

        def __repl__(self):
            return f'User{self.user_id}-contact{self.contact_id}'

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}',
                                    echo=False,
                                    pool_recycle=7200,
                                    connect_args={'check_same_thread': False}
                                    )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()  # очищаем таблицу активных юзеров при старте
        self.session.commit()

    def user_login(self, username, ipaddress, port, pubkey=None):
        """
        Метод логина пользователя, проверяет что такой пользователь есть (если нет - создает)
        и записывает данные в активные и историю входов
        """
        find_login = self.session.query(self.Users).filter_by(login=username)
        # ищем пользователя с таким же логином
        if find_login.count():  # если есть то берем его логин и записываем в историю входа и в активные
            user = find_login.first()
            user.last_login = datetime.datetime.now()
            # проверяем не изменился ли ключ, если изменился то обновляем
            if user.pubkey != pubkey:
                user.pubkey = pubkey
            new_log_record = self.UserLoginHistory(user.id, ipaddress, port, datetime.datetime.now())
            new_active = self.ActiveUsers(user.id, ipaddress, port, datetime.datetime.now())
            self.session.add(new_log_record)
            self.session.add(new_active)
            self.session.commit()  # все записали
        else:  # если нет то бросаем исключение
            raise ValueError('Пользователь не зарегистрирован.')

    def getactive(self):
        """Метод возвращающий активных пользователей"""
        active_users = self.session.query(self.Users.login, self.ActiveUsers.ipaddress, self.ActiveUsers.port,
                                          self.ActiveUsers.login_time).join(self.Users).all()
        return active_users

    def users_list(self):
        """Метод возвращающий список известных пользователей со временем последнего входа."""
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.Users.login,
            self.Users.last_login
        )
        # Возвращаем список кортежей
        return query.all()

    def getall(self):
        """Метод возвращающий всех пользователй"""
        all_users = self.session.query(self.Users.id, self.Users.login).all()
        return all_users

    def history_log(self, name=''):
        """Метод возвращающий историю входов"""
        logs = self.session.query(self.Users.login, self.UserLoginHistory.ipaddress, self.UserLoginHistory.port,
                                  self.UserLoginHistory.login_time).join(self.Users)

        return logs.all() if name == '' else logs.filter_by(login=name).all()

    def add_user(self, name, passwd_hash):
        """
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        """
        user_row = self.Users(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        self.session.query(self.ActiveUsers).filter_by(id=user.id).delete()
        self.session.query(self.UserLoginHistory).filter_by(user_id=user.id).delete()
        self.session.query(self.Contacts).filter_by(user_id=user.id).delete()
        self.session.query(
            self.Contacts).filter_by(
            contact_id=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Users).filter_by(login=name).delete()
        self.session.commit()

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.Users).filter_by(login=name).first()
        return user.pubkey

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.Users).filter_by(login=name).count():
            return True
        else:
            return False

    def user_logout(self, username):
        """Метод обрабатывающий выход пользователя. Удаляет из таблицы активных"""
        try:
            # Запрашиваем пользователя, что покидает нас
            user = self.session.query(self.Users).filter_by(login=username).first()
            # Удаляем его из таблицы активных пользователей.
            self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
            self.session.commit()
        except:
            pass

    def add_contact(self, user, contact):
        """Метод добавления контакта пользователя"""
        user = self.session.query(self.Users).filter_by(login=user).first()
        contact = self.session.query(self.Users).filter_by(login=contact).first()
        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.Contacts).filter_by(user_id=user.id, contact_id=contact.id).count():
            print('Такой контакт уже есть')
            return
        else:
            new_contact = self.Contacts(user.id, contact.id)
            self.session.add(new_contact)
            self.session.commit()

    def del_contact(self, user, contact):
        """Метод удаления контакта пользователя"""
        # Получаем ID пользователей
        user = self.session.query(self.Users).filter_by(login=user).first()
        contact = self.session.query(self.Users).filter_by(login=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            print('Нет такого котнтакта')
            return
        # Удаляем контакт
        print(self.session.query(self.Contacts).
              filter(self.Contacts.user_id == user.id, self.Contacts.contact_id == contact.id).delete())
        self.session.commit()

    def message_history(self):
        """Метод возвращающий данные по отправленным и принятым сообщениям пользователя"""
        query = self.session.query(
            self.Users.login,
            self.Users.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Users, self.Users.id == self.UsersHistory.user)
        # Возвращаем список кортежей
        # print(query.all())
        return query.all()
        # return [('user1', '2022-11-28 01:49:11.843131', 9, 10)]

    def get_user_contacts(self, user):
        """Метод получения контактов пользователя"""
        try:
            # ищем указанного пользователя
            user = self.session.query(self.Users).filter_by(login=user).one()
            # contacts = self.session.query(self.Contacts.user_id,).filter_by(user_id=user_id).all()
        except:
            contacts = []
        else:
            # Запрашиваем его список контактов
            query = self.session.query(self.Contacts.contact_id, self.Users.login). \
                filter_by(user_id=user.id). \
                join(self.Users, self.Contacts.contact_id == self.Users.id)
            # выбираем только имен контактов и возвращаем
            contacts = [contact[1] for contact in query.all()]
            print(contacts)
        return contacts

    def process_message(self, sender, recipient):
        """Метод обновляющий счетчики отправленных и полученых сообщений"""
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.Users).filter_by(login=sender).first().id
        recipient = self.session.query(self.Users).filter_by(login=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()


if __name__ == '__main__':
    client = ServerStorage('server_base.db3')
    # print(client.getactive())
    # client.user_login('ivanov', '127.0.0.1', 55)
    # client.user_login('pppetrov', '127.0.0.1', 11)
    # client.user_login('kuznetsov', '127.0.0.127', 99)
    # client.user_login('pppetroff', '127.0.0.99', 22)
    # # print(client.getall()))
    # print(client.getactive())
    # client.user_logout(1)
    # print(client.getactive())
    # print(client.history_log())
    # print(client.history_log('ivanov'))
    # print(client.get_user_contacts(1))
    # client.add_contact('ivanov', 'pppetrov')
    # client.add_contact(1, 3)
    # client.add_contact(1, 4)
    # print(client.get_user_contacts(1))
    # client.del_contact(1, 2)
    # client.del_contact(1, 4)
    # client.add_contact(1, 3)
    # client.del_contact(1, 4)
    # print(client.get_user_contacts('ivanov'))
    client.message_history()
