import platform
import subprocess
import time
from subprocess import Popen
import os
import signal
# сколько клиентов запускать
client_count = 2

dir_path = os.path.dirname(os.path.realpath(__file__))
if platform.system() == 'Windows':
    from subprocess import CREATE_NEW_CONSOLE
    enterpriter = 'python'
else:
    enterpriter = 'gnome-terminal -- python3'
process = []

path_client = os.path.join(dir_path, 'client')
path_server = os.path.join(dir_path, 'server')

def run_one(that: str):
    if platform.system() == 'Windows':
        process.append(Popen(that, creationflags=CREATE_NEW_CONSOLE))
    else:
        process.append(Popen(that, shell=True, stdout=subprocess.PIPE))


def kill_processes():
    if platform.system() == 'Windows':
        for p in process:
            p.kill()
        process.clear()
    else:
        while process:
            p = process.pop()
            # print(p)

            p.kill()
            p.terminate()


while True:
    user_answer = input("Запустить сервер(s)\nЗапустить клиентов (c)\nЗапустить все (а)"
                        "\nЗапустить cli клиента (cc)\nЗакрыть все (x)\nВыйти(q):\n")
    if user_answer == 'q':
        kill_processes()
        break
    elif user_answer == 's':
        run_one(f'{enterpriter} {os.path.join(path_server, "server.py")} -a "127.0.0.1" -p "-7777"')

    elif user_answer == 'c':
        for _ in range(client_count):
            run_one(f'{enterpriter} {os.path.join(path_client, "transport.py")} -n user{_}')

    elif user_answer == 'cc':
        run_one(f'{enterpriter} {os.path.join(path_client, "client.py")} -n user')

    elif user_answer == 'g':
        run_one(f'{enterpriter} {os.path.join(path_client, "transport.py")} -n user')

    elif user_answer == 'a':
        run_one(f'{enterpriter} {os.path.join(path_server, "server.py")} -a "127.0.0.1" -p "7777"')
        time.sleep(0.5)  # ждем чтобы стартанул сервер
        for _ in range(client_count):
            run_one(f'{enterpriter} {os.path.join(path_client, "transport.py")} -n user{_}')

    elif user_answer == 'x':
        kill_processes()


