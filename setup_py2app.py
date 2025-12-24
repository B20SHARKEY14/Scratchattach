from setuptools import setup

APP = ["main.py"]
OPTIONS = {
    'argv_emulation': True,
    'compressed': True,
    'optimize': 2,
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
