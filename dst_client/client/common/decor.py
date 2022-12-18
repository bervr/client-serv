import inspect
import logging
import sys
import traceback


if sys.argv[0].find('client.py') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


def func_log(in_function):
    """функция декоратор логирующая вызовы функций"""
    def wrapper(*args, **kwargs):
        result = in_function(*args, **kwargs)
        LOGGER.debug(f"Вызвана функция {in_function.__name__} "
                     f"из функции {traceback.format_stack()[0].strip().split()[-1]} "
                     f"а точнее из {inspect.stack()[1][3]} с параметрами {args} {kwargs},"
                     f" вызов из модуля {in_function.__name__}", stacklevel=2)
        return result
    return wrapper


class Log:
    def __call__(self, in_function):
        """функция декоратор логирующая вызовы методов"""
        def wrapper(*args, **kwargs):
            result = in_function(*args, **kwargs)
            LOGGER.debug(f"Вызвана функция {in_function.__name__} "
                         f"из функции {traceback.format_stack()[0].strip().split()[-1]} "
                         f"а точнее из {inspect.stack()[1][3]} с параметрами {args} {kwargs},"
                         f" вызов из модуля {in_function.__name__}", stacklevel=2)
            return result
        return wrapper
