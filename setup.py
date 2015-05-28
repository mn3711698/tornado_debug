# coding:utf8
from setuptools import setup, find_packages

readme = open('README.md').read()

setup(
    name="tornado-debug",
    version="${version}",
    description="debug tornado web application",
    author="shaolianbo",
    author_email="lianboshao@sohu-inc.com",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'tornado_debug': ['bootstrap/'],
    },
    install_requires=[
        'tornado==2.4.1',
        'redis',
        'jinja2',
    ],
    entry_points={
        'console_scripts': [
            'tor-debug = tornado_debug.main:main',
            'tor-debug-test = tornado_debug.agent:initialize',
            'tor-server = tornado_debug.server.server:run',
        ]
    },
    long_description=readme
)
