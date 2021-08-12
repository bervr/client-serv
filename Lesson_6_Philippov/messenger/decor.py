import inspect
import logging
import sys
import traceback
import logs.conf.server_log_config
import logs.conf.client_log_config


# print(sys.argv[0])
if sys.argv[0].find('client.py') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def func_log(in_function):
    def wrapper(*args, **kwargs):
        result = in_function(*args, **kwargs)
        LOGGER.debug(f"Вызвана функция {in_function.__name__} с параметрами \n{args} {kwargs}", stacklevel=2)

        return result
    return wrapper

class Log:
    def __call__(self, in_function):
        def wrapper(*args, **kwargs):
            result = in_function(*args, **kwargs)
            LOGGER.debug(f"Вызвана функция {in_function.__name__}  с параметрами \n{args}-25s\n{kwargs}-25s", stacklevel=2)
            return result
        return wrapper


def func_call(in_function):
    def wrapper(*args, **kwargs):
        result = in_function(*args, **kwargs)
        LOGGER.debug(f"Вызов функции {in_function.__name__} был произведен  "
                     f"из функции {inspect.stack()[1][3]} "
                     f"а точнее из {traceback.format_stack()[0].strip().split()[-1]}", stacklevel=2)
        return result
    return wrapper


