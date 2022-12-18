"""Утилиты"""
import argparse
import json

from common.variables import MAX_PACKAGE_LENGTH, ENCODING, DEFAULT_PORT, DEFAULT_IP_ADDRESS
from common.decor import func_log, Log


@Log()
def get_message(client):
    """Функция декодирующая сообщение из байтов в JSON"""
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@func_log
def send_message(sock, message):
    """Функция кодирующаяя сообщение для отправки из JSON в байты"""
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)


def create_arg_parser(default_port, default_address):
    """Функция парсер аргументов командной строки"""
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=default_port, type=int, nargs='?')
        parser.add_argument('-a', default=default_address, nargs='?')
        parser.add_argument('-m', default='listen', nargs='?')
        parser.add_argument('-n', default='', nargs='?')
        parser.add_argument('-w', default='', nargs='?')
        return parser
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except ValueError:
        return 'В качестве порта может быть указано только число в диапазоне от 1024 до 65535.'

