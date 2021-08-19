import platform
from subprocess import Popen
# сколько клиентов запускать
client_count = 3


if platform.system() == 'Windows':
    from subprocess import CREATE_NEW_CONSOLE
    enterpriter = 'python'
else:
    enterpriter = 'gnome-terminal -- python3'
process = []


def run_one(that: str):
    print(that)
    if platform.system() == 'Windows':
        process.append(Popen(that, creationflags=CREATE_NEW_CONSOLE))
    else:
        process.append(Popen(that, shell=True))


def kill_processes():
    if platform.system() == 'Windows':
        for p in process:
            p.kill()
        process.clear()
    else:
        while process:
            p = process.pop()
            p.kill()
            p.terminate()


while True:
    user_answer = input("Запустить сервер(s)\nЗапустить клиентов (c)\nЗапустить все (а)\nЗакрыть все (x)\nВыйти(q): ")
    if user_answer == 'q':
        kill_processes()
        break
    elif user_answer == 's':
        run_one(f'{enterpriter} server.py')

    elif user_answer == 'c':
        for _ in range(client_count):
            run_one(f'{enterpriter} client.py')

    elif user_answer == 'a':
        run_one(f'{enterpriter} server.py')
        for _ in range(client_count):
            run_one(f'{enterpriter} client.py')

    elif user_answer == 'x':
        kill_processes()


