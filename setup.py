import codecs
from setuptools import setup


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="ss-py-mu",
    version="1.0.0",
    license='http://www.apache.org/licenses/LICENSE-2.0',
    description="A fast tunnel proxy that help you get through firewalls (Multi-user version)",
    author='clowwindy',
    author_email='clowwindy42@gmail.com',
    url='https://github.com/dylanchu/ss-py-mu',
    packages=['shadowsocks', 'shadowsocks.crypto'],
    include_package_data=True,
    package_data={
        'shadowsocks': ['README.rst', 'LICENSE', 'shadowsocks/*.ini', 'shadowsocks/*.html']
    },
    install_requires=['cymysql'],
    entry_points="""
    [console_scripts]
    ss-py-mu = shadowsocks.servers:main
    ss-py-mu-reminder-mail = shadowsocks.reminder_mail:main
    """,
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: Proxy Servers',
    ],
    long_description=long_description,
)
