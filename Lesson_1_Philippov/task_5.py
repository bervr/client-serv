"""
Задание 5.

Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
преобразовать результаты из байтовового в строковый тип на кириллице.

Подсказки:
--- используйте модуль chardet, иначе задание не засчитается!!!
"""

import subprocess
import chardet

def run_ping(args):
    for item in args:
        # print(item)
        new_ping = subprocess.Popen(item, stdout=subprocess.PIPE)
        for line in new_ping.stdout:
            result = chardet.detect(line)
            line = line.decode(result['encoding'])  #  .encode('utf-8')
            print(line)  #   .decode('utf-8'))



ARGS =(['ping', 'localhost', '-c 4'],['ping', 'ya.ru', '-c 4'])
run_ping(ARGS)
