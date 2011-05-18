#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_scripts import install_scripts

class post_install(install_scripts):

    def run(self):
        install_scripts.run(self)

        from shutil import move
        for i in self.get_outputs():
            n = i.replace('.py', '')
            move(i, n)
            print "moving '{0}' to '{1}'".format(i, n)

ID = 'org.cream.HotkeyManager'

data_files = [
    ('share/cream/{0}'.format(ID), ['src/manifest.xml']),
    ('share/dbus-1/services', ['src/org.cream.HotkeyManager.service'])
]

setup(
    name = 'hotkey-manager',
    version = '0.1.1',
    author = 'The Cream Project (http://cream-project.org)',
    url = 'http://github.com/cream/hotkey-manager',
    data_files = data_files,
    cmdclass={'install_scripts': post_install},
    scripts = ['src/hotkey-manager.py']
)
