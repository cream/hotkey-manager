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

import cream
import cream.ipc

class HotkeyBinding(gobject.GObject):
    __gsignals__ = {
        'activate': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_INT))
        }

    def __init__(self):

        gobject.GObject.__init__(self)

        self.keymap = gtk.gdk.keymap_get_default()
        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.screen.root

        self.hotkeys = []


    def add_hotkey(self, hotkey):

        keyval, modifier_mask = gtk.accelerator_parse(hotkey)
        if not keyval and not modifiers:
            self.keycode = None
            self.modifier_mask = None
            return
        
        keycode = self.keymap.get_entries_for_keyval(keyval)[0][0]
        modifier_mask = int(modifier_mask)

        self.hotkeys.append((keycode, modifier_mask))
        self.root.grab_key (keycode, modifier_mask, True, X.GrabModeAsync, X.GrabModeSync)
        self.display.flush()


    def ungrab(self):

        for keycode, modifier_mask in self.hotkeys:
            self.root.ungrab_key (keycode, modifier_mask, self.root)


    def handler(self, keyval, mask):

        gtk.gdk.threads_enter()
        self.emit("activate", keyval, mask)
        gtk.gdk.threads_leave()
        return False


    def run (self):

        self.running = True
        wait_for_release = False
        while self.running:
            event = self.display.next_event()
            if event.type == X.KeyPress:
                keyval = self.keymap.get_entries_for_keycode(event.detail)[0][0]
                modifier_mask = event.state
                gobject.idle_add(self.handler, keyval, modifier_mask)
            self.display.allow_events(X.AsyncKeyboard, event.time)


    def listen(self):

        thread.start_new_thread(self.run, ())


    def stop (self):

        self.running = False
        self.ungrab()
        self.display.close()


class HotkeyManager(cream.Module, cream.ipc.Object):

    __ipc_signals__ = {
        'activate': 'ii'
        }

    def __init__(self):

        cream.Module.__init__(self)
        cream.ipc.Object.__init__(self,
            'org.cream.hotkeys',
            '/org/cream/hotkeys'
        )

        self.binding = HotkeyBinding()
        self.binding.connect('activate', self.handler)
        self.binding.listen()


    def handler(self, binding, keyval, modifier_mask):

        self.messages.debug("'{0}' was pressed...".format(gtk.accelerator_get_label(keyval, modifier_mask)))
        self.emit_signal('activate', keyval, modifier_mask)


    @cream.ipc.method('s')
    def register_hotkey(self, hotkey):

        self.binding.add_hotkey(hotkey)


if __name__ == '__main__':
    hotkeymanager = HotkeyManager()
    hotkeymanager.main()
