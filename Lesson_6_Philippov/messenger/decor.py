import logging
import sys

import logs.conf.server_log_config
import logs.conf.client_log_config
if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def func_log(in_function):
    def wrapper(*args, **kwargs):
        result = in_function(*args, **kwargs)
        LOGGER.debug(f"вызвана функция {in_function.__name__} с параметрами {args} {kwargs},"
                     f" вызов из модуля {in_function.__name__}")
        return result
    return wrapper()

