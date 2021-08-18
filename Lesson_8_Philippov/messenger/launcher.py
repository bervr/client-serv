import platform
from subprocess import Popen

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


while True:
    user_answer = input("Запустить сервер(s)\nЗапустить клиентов (c)\nЗакрыть все (x)\nВыйти(q): ")
    if user_answer == 'q':
        break
    elif user_answer == 's':
        run_one(f'{enterpriter} server.py')

    elif user_answer == 'c':
        for _ in range(7):
            run_one(f'{enterpriter} client.py')

    elif user_answer == 'x':
        for p in process:
            p.kill()
        process.clear()
