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

gui_client = os.path.join(dir_path, 'client')

def run_one(that: str):
    # print(that)
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
            # for pid in p.stdout:   #todo
            #     print(p.stdout)
            #     os.kill(int(pid), signal.SIGTERM)
            #     try:
            #         os.kill(int(pid),0)
            #         raise Exception("Can't kill the process")
            #     except OSError as err:
            #         continue


while True:
    user_answer = input("Запустить сервер(s)\nЗапустить клиентов (c)\nЗапустить все (а)"
                        "\nЗапустить gui клиента (g)\nЗакрыть все (x)\nВыйти(q):\n")
    if user_answer == 'q':
        kill_processes()
        break
    elif user_answer == 's':
        run_one(f'{enterpriter} server.py -a "127.0.0.1" -p "-7777"')

    elif user_answer == 'c':
        for _ in range(client_count):
            # print(f'{enterpriter} client.py -n user{_}')
            run_one(f'{enterpriter} client.py -n user{_}')
    elif user_answer == 'g':
        run_one(f'{enterpriter} {os.path.join(gui_client, "transport.py")}')

    elif user_answer == 'a':
        run_one(f'{enterpriter} server.py')
        time.sleep(0.5)  # ждем чтобы стартанул сервер
        run_one(f'{enterpriter} client/transport.py')
        for _ in range(client_count):
            run_one(f'{enterpriter} client.py -n user{_}')

    elif user_answer == 'x':
        kill_processes()


