import datetime

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_


Base = declarative_base()


class ClientStorage:
    """Основной базы данных клиента мессенджера"""

    class Contacts(Base):
        """Таблица контактов"""
        __tablename__ = 'contacts'
        contact_id = Column(Integer, primary_key=True)
        contact_name = Column(String)

        def __init__(self, contact_name):
            self.contact_name = contact_name

        def __repl__(self):
            return f'Contact{self.contact_id}({self.contact_name})'

    class MessageHistory(Base):
        """Таблица истории сообщений"""
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        sender_id = Column(ForeignKey('contacts.contact_id'))
        receiver_id = Column(ForeignKey('contacts.contact_id'))
        text = Column(String)
        message_time = Column(DateTime)

        def __init__(self, sender_id, receiver_id, text, message_time):
            self.sender_id = sender_id
            self.receiver_id = receiver_id
            self.text = text
            self.message_time = message_time

        def __repl__(self):
            return f'Message from {self.sender_id} to {self.receiver_id} at {self.message_time} is: {self.text}'

    class KnownUsers(Base):
        """Таблица известных пользователей"""
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        def __init__(self, user):
            self.id = None
            self.username = user

    def __init__(self, path):
        self.engine = create_engine(f'sqlite:///{path}',
                                    pool_recycle=7200,
                                    echo=False,
                                    connect_args={'check_same_thread': False}
                                    )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()
        if not self.session.query(self.Contacts).filter_by(contact_name='me').all():
            me = self.Contacts('me')
            self.session.add(me)  # добавили себя в список контактов
            self.session.commit()

    def get_history(self, username='me'):
        """Метод возвращающий историю переписки с конкретным пользователем.
        Если имя пользователя не передано, то возвращает всю историю со всеми пользователями"""
        try:
            user = self.session.query(self.Contacts.contact_id).filter_by(contact_name=username).first()[0]
        except:
            user = 1
        if user == 1:
            history = self.session.query(self.MessageHistory.sender_id,
                                         self.MessageHistory.receiver_id,
                                         self.MessageHistory.text,
                                         self.MessageHistory.message_time).all()
        else:
            history = self.session.query(self.MessageHistory.sender_id,
                                         self.MessageHistory.receiver_id,
                                         self.MessageHistory.text,
                                         self.MessageHistory.message_time). \
                filter(or_(self.MessageHistory.sender_id == user,
                           self.MessageHistory.receiver_id == user)).all()

        return history

    def write_log(self, sender, receiver, text, time=datetime.datetime.now()):
        """Метод записывающий в историю сообщений"""
        sender_id = self.session.query(self.Contacts.contact_id).filter_by(contact_name=sender) \
            if sender != 'me' else 1
        receiver_id = self.session.query(self.Contacts.contact_id).filter_by(contact_name=receiver) \
            if receiver != 'me' else 1
        new_message = self.MessageHistory(sender_id, receiver_id, text, time)
        self.session.add(new_message)
        self.session.commit()

    def add_users(self, users_list):
        """ Метод добавления известных пользователей.
        Пользователи получаются только с сервера, поэтому таблица очищается."""
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def add_contact(self, contact_name):
        """Метод добавления новых контактов"""
        try:
            find_contact = self.session.query(self.Contacts).filter_by(contact_name=contact_name).first()
        except:
            pass
        else:
            if not find_contact:
                new_contact = self.Contacts(contact_name)
                self.session.add(new_contact)
                self.session.commit()
            elif find_contact[0]:
                # print('Нельзя создать себя')
                pass
            else:
                # print('Такой контакт уже есть')
                pass

    def contacts_clear(self):
        '''Метод очищающий таблицу со списком контактов.'''
        self.session.query(self.Contacts).delete()

    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(contact_name=contact).count():
            return True
        return False

    def check_user(self, user):
        """Метод проверяющий что пользователь есть в списке известных"""
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        return False

    def get_users(self):
        """Метод возвращающяя список известных пользователей"""
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    def del_contact(self, contact):
        """Метод удаления контакта"""
        if contact != 'me':
            self.session.query(self.Contacts).filter_by(contact_name=contact).delete()
            self.session.commit()

    def get_user_contacts(self):
        """Метод получения списка контактов"""
        try:
            contacts = self.session.query(self.Contacts.contact_id, self.Contacts.contact_name).all()
        except:
            contacts = []
        # return contacts
        return [contact[1] for contact in contacts]


if __name__ == '__main__':
    client = ClientStorage('user.db3')

    # client.add_contact('Uasya')
    # client.add_contact('Uova')
    # client.add_contact(0)
    # client.del_contact('Uova')
    # client.add_contact('Yulya')
    print(client.get_user_contacts())
    # client.write_log(1, 3, 'привет')
    # client.write_log(3, 1, 'сам такой')
    # client.write_log(1, 3, 'как дела')
    # client.write_log(1, 2, 'ghbdtn')
    # client.write_log(3, 1, 'че хотел?')
    # client.write_log(1, 3, 'домашку сделала?')
    print(client.get_history('user'))
