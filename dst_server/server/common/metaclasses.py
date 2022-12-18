import dis
import socket


class ServerVerifier(type):
    """
    Метакласс ServerVerifier, выполняет базовую проверку класса «Сервер»:
    отсутствие вызовов connect для сокетов и использование сокетов для работы по TCP
    """

    def __new__(cls, name, bases, dict):
        new_class = super(ServerVerifier, cls).__new__(cls, name, bases, dict)
        for func in new_class.__dict__:
            try:
                ret = dis.get_instructions(new_class.__dict__[func])
            except TypeError:
                pass
            except SyntaxError:
                pass
            else:
                for i in ret:
                    if i.argval == 'connect':
                        raise Exception(f"Method connect can't be used in this module: {func}")
                    elif i.argval == 'SOCK_DGRAM':
                        raise Exception(f"UDP connection not supported in this version. Method: {func}")
        return new_class


class ClientVerifier(type):
    """
    Метакласс ClientVerifier, выполняет базовую проверку класса «Клиент»
    отсутствие вызовов accept и listen для сокетов;
    использование сокетов для работы по TCP;
    отсутствие создания сокетов на уровне классов, то есть отсутствие конструкций такого вида:
    class Client: s = socket(). Для проверок используется модуль dis:
    """

    def __new__(cls, name, bases, dict):
        client_class = super(ClientVerifier, cls).__new__(cls, name, bases, dict)
        for func, value in client_class.__dict__.items():
            if type(value) is type(socket.socket()):
                raise Exception(f"Creation socket in this level is forbidden: {func}")
            try:
                ret = dis.get_instructions(client_class.__dict__[func])
            except TypeError:
                pass
            except SyntaxError:
                pass
            else:
                for i in ret:
                    if i.argval == 'accept' or i.argval == 'listen':
                        raise Exception(f"Accept and listen method's can't be used in this module: {func}")
                    elif i.argval == 'SOCK_DGRAM':
                        raise Exception(f"UDP connection not supported in this version. Method: {func}")
        return client_class
