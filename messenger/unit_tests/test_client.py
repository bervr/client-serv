import os
import sys
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, PRESENCE, TIME, USER, ERROR
from dst_client.client import MsgClient


class Time:
    def time(self):
        return 1111.111


time = Time()


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = MsgClient()

    def test_create_presence(self):
        new_test = self.client.create_presence()
        new_test[TIME] = 1111.111
        self.assertEqual(new_test, {ACTION: PRESENCE, TIME: time.time(), USER: {ACCOUNT_NAME: 'Guest'}})

    def test_process_ans_200(self):
        self.assertEqual(self.client.process_ans({RESPONSE: 200}), '200 : OK')

    def test_process_ans_400(self):
        self.assertEqual(self.client.process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_process_no_ans(self):
        self.assertRaises(ValueError, self.client.process_ans, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
