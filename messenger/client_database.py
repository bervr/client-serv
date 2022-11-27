from time import strftime

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
import datetime

Base = declarative_base()

class ClientStorage:
    class Contacts(Base):
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        contact_id = Column(Integer, unique=True)
        contact_name = Column(String)

        def __init__(self, contact_id, contact_name=''):
            self.contact_id = contact_id
            self.contact_name = contact_name

        def __repl__(self):
            return f'Contact{self.contact_id}({self.contact_name})'

    class MessageHistory(Base):
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
        __tablename__ = 'known_users'
        id = Column(Integer, primary_key=True)
        username = Column(String)
        def __init__(self, user):
            self.id = None
            self.username = user

    def __init__(self, name):
        self.engine = create_engine(f'sqlite:///client_{name}.db3',
                                    pool_recycle = 7200,
                                    echo=False,
                                    connect_args={'check_same_thread': False}
                                    )
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        if self.session.query(self.Contacts).filter_by(contact_id=0).all() == []:
            me = self.Contacts(0, 'me')
            self.session.add(me)  # добавили себя в список контактов
            self.session.commit()

    def get_history(self, username='me'):
        try:
            user = self.session.query(self.Contacts.contact_id).filter_by(contact_name=username).first()[0]
        except:
            user = 0
        if user == 0:
            history = self.session.query(self.MessageHistory.sender_id,
                                     self.MessageHistory.receiver_id,
                                     self.MessageHistory.text,
                                     self.MessageHistory.message_time).all()
        else:
            history = self.session.query(self.MessageHistory.sender_id,
                                         self.MessageHistory.receiver_id,
                                         self.MessageHistory.text,
                                         self.MessageHistory.message_time).\
                filter(or_(self.MessageHistory.sender_id == user,
                           self.MessageHistory.receiver_id == user)).all()

        return history

    def write_log(self, sender_id, receiver_id, text, time=datetime.datetime.now()):
        new_message = self.MessageHistory(sender_id, receiver_id, text, time)
        self.session.add(new_message)
        self.session.commit()

    # Функция добавления известных пользователей.
    # Пользователи получаются только с сервера, поэтому таблица очищается.
    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def add_contact(self, contact_id, contact_name=''):
        find_contact = self.session.query(self.Contacts.contact_id).filter_by(contact_id=contact_id).all()
        if contact_id == 0:
            pass
            # print('Нельзя создать себя')
        elif find_contact:
            pass
            # print('Такой контакт уже есть')
        else:
            new_contact = self.Contacts(contact_id, contact_name)
            self.session.add(new_contact)
            self.session.commit()

    def check_contact(self):
        pass

    def del_contact(self, contact):
        if contact != 'me':
            self.session.query(self.Contacts).filter_by(contact_name=contact).delete()
            self.session.commit()

    def get_user_contacts(self):
        try:
            contacts = self.session.query(self.Contacts.contact_id, self.Contacts.contact_name).all()
        except:
            contacts = []
        return contacts


if __name__ == '__main__':
    client = ClientStorage('222')

    client.add_contact(1, 'Uasya')
    client.add_contact(2, 'Uova')
    client.add_contact(0)
    client.del_contact(0)
    client.add_contact(3, 'Yulya')
    print(client.get_user_contacts())
    client.write_log(0, 3, 'привет')
    client.write_log(3, 0, 'сам такой')
    client.write_log(0, 3, 'как дела')
    client.write_log(0, 2, 'ghbdtn')
    client.write_log(3, 0, 'че хотел?')
    client.write_log(0, 3, 'домашку сделала?')
    print(client.get_history('Uova'))





