import json
import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, ERROR, ENCODING
from common.utils import send_message, get_message


class TestSocket:
    # тестовый сокет
    def __init__(self, test_data):
        self.test_data = test_data
        self.encoded_msg = None
        self.received_msg = None

    def send(self, message):
        test_message_json = json.dumps(self.test_data)
        self.encoded_msg = test_message_json.encode(ENCODING)
        self.received_msg = message

    def recv(self, max_len):
        test_message_json = json.dumps(self.test_data)
        return test_message_json.encode(ENCODING)


class TestUtils(unittest.TestCase):
    # def SetUp(self):
    test_dict = {
        ACTION: PRESENCE,
        TIME: 65432,
        USER: {
            ACCOUNT_NAME: 'test_user'
        }
    }

    bad_dict = {
        ACTION: 123,
        USER: {
        }
    }
    test_recv_ok = {RESPONSE: 200}
    test_recv_error = {RESPONSE: 400, ERROR: 'Bad Request'}

    def test_send_message(self):
        test_socket = TestSocket(self.test_dict)
        send_message(test_socket, self.test_dict)
        self.assertEqual(test_socket.encoded_msg, test_socket.received_msg)
        with self.assertRaises(Exception):
            send_message(test_socket, test_socket)
            # строго говоря оно тут не только словарь принимает

    def test_get_message(self):
        test_recv_socket_ok = TestSocket(self.test_recv_ok)
        self.assertEqual(get_message(test_recv_socket_ok), self.test_recv_ok)
        test_recv_socket_error = TestSocket(self.test_recv_error)
        self.assertEqual(get_message(test_recv_socket_error), self.test_recv_error)
        test_socket = TestSocket('123')
        with self.assertRaises(Exception):
            get_message(test_socket)


if __name__ == '__main__':
    unittest.main()
