"""Утилиты"""

import json
import os
import sys

from common.variables import MAX_PACKAGE_LENGTH, ENCODING
sys.path.append(os.path.join(os.getcwd(), '..'))
from decor import func_log


@func_log
def get_message(client):
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
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)