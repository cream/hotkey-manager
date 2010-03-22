#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import os

from Xlib.display import Display
from Xlib import X
import gobject
import gtk.gdk
import thread
import weakref

import cream
import cream.ipc
from cream.util import random_hash

class HotkeyBinding(gobject.GObject):
    __gsignals__ = {
        'hotkey-activated': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT))
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.keymap = gtk.gdk.keymap_get_default()
        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.screen.root

        self.hotkeys = []


    def add_hotkey(self, keyval, modifier_mask):

        if not keyval and not modifiers:
            self.keycode = None
            self.modifier_mask = None
            return

        keycode = self.keymap.get_entries_for_keyval(keyval)[0][0]
        modifier_mask = int(modifier_mask)

        self.hotkeys.append((keycode, modifier_mask))
        self.root.grab_key(keycode, modifier_mask, True, X.GrabModeAsync, X.GrabModeSync)
        self.display.flush()


    def ungrab(self):

        for keycode, modifier_mask in self.hotkeys:
            self.root.ungrab_key (keycode, modifier_mask, self.root)


    def handler(self, keyval, mask):

        gtk.gdk.threads_enter()
        self.emit("hotkey-activated", keyval, mask)
        gtk.gdk.threads_leave()
        return False


    def run (self):

        self.running = True
        wait_for_release = False
        while self.running:
            try:
                event = self.display.next_event()
                if event.type == X.KeyPress:
                    keyval = self.keymap.get_entries_for_keycode(event.detail)[0][0]
                    modifier_mask = event.state
                    gobject.idle_add(self.handler, keyval, modifier_mask)
                self.display.allow_events(X.AsyncKeyboard, event.time)
            except:
                self.display.allow_events(X.AsyncKeyboard, X.CurrentTime)


    def listen(self):

        thread.start_new_thread(self.run, ())


    def stop (self):

        self.running = False
        self.ungrab()
        self.display.close()


class HotkeyBroker(cream.ipc.Object):

    __gsignals__ = {
        'hotkey-added': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        'hotkey-removed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT)),
        }

    __ipc_signals__ = {
        'hotkey_activated': ('s', 'org.cream.hotkeys.broker'),
        }

    def __init__(self, manager):

        cream.ipc.Object.__init__(self,
            'org.cream.hotkeys',
            '/org/cream/hotkeys/broker_{0}'.format(random_hash(bits=20))
        )

        self.hotkeys = {}
        self.hotkeys_by_action = {}

        self.manager = weakref.ref(manager)


    def hotkey_activated_cb(self, keyval, modifier_mask):

        if self.hotkeys.has_key((keyval, modifier_mask)):
            self.emit_signal('hotkey_activated', self.hotkeys[(keyval, modifier_mask)][0])


    @cream.ipc.method('ss', 'b', interface='org.cream.hotkeys.broker')
    def set_hotkey(self, action, hotkey):

        keyval, modifier_mask = gtk.accelerator_parse(hotkey)
        if self.hotkeys_by_action.has_key(action):
            del self.hotkeys[self.hotkeys_by_action[action]]
            del self.hotkeys_by_action[action]
        self.hotkeys[(keyval, modifier_mask)] = (action, hotkey)
        self.hotkeys_by_action[action] = (keyval, modifier_mask)
        self.manager().set_hotkey(keyval, modifier_mask, self)


class HotkeyManager(cream.Module, cream.ipc.Object):

    def __init__(self):

        cream.Module.__init__(self)
        cream.ipc.Object.__init__(self,
            'org.cream.hotkeys',
            '/org/cream/hotkeys'
        )

        self.hotkeys = {}

        self.binding = HotkeyBinding()
        self.binding.connect('hotkey-activated', self.handler)
        self.binding.listen()


    def handler(self, binding, keyval, modifier_mask):

        if self.hotkeys.has_key((keyval, modifier_mask)):
            broker = self.hotkeys[(keyval, modifier_mask)]
            broker.hotkey_activated_cb(keyval, modifier_mask)


    def set_hotkey(self, keyval, modifier_mask, broker):

        self.hotkeys[(keyval, int(modifier_mask))] = broker
        self.binding.add_hotkey(keyval, int(modifier_mask))


    @cream.ipc.method('', 'o')
    def register(self):

        b = HotkeyBroker(self)
        return b.__dbus_object_path__


if __name__ == '__main__':
    hotkeymanager = HotkeyManager()
    hotkeymanager.main()
