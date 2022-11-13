import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import RESPONSE, ERROR
from server import MsgServer


class TestServer(unittest.TestCase):
    response_ok = {RESPONSE: 200}
    response_err = {RESPONSE: 400, ERROR: 'Bad Request'}

    #
    def setUp(self):
        self.server = MsgServer()

    def test_process_client_message_correct(self):
        self.assertEqual(self.server.process_client_message({'action': 'presence', 'time': 1573760672.167031,
                                                             'user': {'account_name': 'Guest'}}), self.response_ok)

    def test_process_client_message_action(self):
        self.assertEqual(self.server.process_client_message({'time': 1573760672.167031,
                                                             'user': {'account_name': 'Guest'}}), self.response_err)

    def test_process_client_message_action_err(self):
        self.assertEqual(self.server.process_client_message({'action': 'test', 'time': 1573760672.167031,
                                                             'user': {'account_name': 'Guest'}}), self.response_err)

    def test_process_client_message_time(self):
        self.assertEqual(self.server.process_client_message({'action': 'presence',
                                                             'user': {'account_name': 'Guest'}}), self.response_err)

    def test_process_client_message_user(self):
        self.assertEqual(self.server.process_client_message({'action': 'presence', 'time': 1573760672.167031,
                                                             }), self.response_err)

    def test_process_client_message_user_name(self):
        self.assertEqual(self.server.process_client_message({'action': 'presence', 'time': 1573760672.167031,
                                                             'user': {'account_name': 'Test'}}), self.response_err)


if __name__ == '__main__':
    unittest.main()
