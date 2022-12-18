from setuptools import find_packages, setup

setup(name="bervr messenger server",
      version="2.1.8",
      description="A server part for messenger",
      author="Aleksandr Filippov",
      author_email="bervrr@gmail.com",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['PyQt5', 'SQLAlchemy', 'pycryptodome', 'pycryptodomex', 'chardet'],
      scripts=['./server/server_run.py']
      )
