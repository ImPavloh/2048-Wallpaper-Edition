from setuptools import setup, find_packages

setup(
    name='2048-Wallpaper-Edition',
    version='1.0.0',
    description='A Python implementation of the 2048 game on your desktop background',
    packages=find_packages(),
    install_requires=[
        'Pillow==8.4.0',
        'keyboard==0.13.5',
    ],
)
