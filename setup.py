from setuptools import setup

setup(
   name='radiobrowserpy',
   version='0.0.1',
   description='Module for making requests to radio-browser.info webservice',
   author='chrismax',
   author_email='chrystler@web.de',
   packages=['radiobrowserpy'],
   install_requires=['requests', 'future'],
)