#!/usr/bin/env python
from __future__ import print_function
import sys

import pygtk
pygtk.require('2.0')

import dbus
from gi.repository import GObject
from gi.repository import Gtk

from account import connection_from_file
from call import IncomingCall, OutgoingCall, get_stream_engine

from telepathy.interfaces import CONN_INTERFACE

class CallWindow(gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        hbox = Gtk.HBox()
        hbox.set_border_width(10)
        vbox = Gtk.VBox()

        output_frame = Gtk.Frame()
        output_frame.set_shadow_type(Gtk.SHADOW_IN)

        preview_frame = Gtk.Frame()
        preview_frame.set_shadow_type(Gtk.SHADOW_IN)

        self.output = Gtk.Socket()
        self.output.set_size_request(400, 300)
        self.preview = Gtk.Socket()
        self.preview.set_size_request(200, 150)

        self.call_button = Gtk.Button('Call')
        self.call_button.connect('clicked', self._call_button_clicked)

        output_frame.add(self.output)
        preview_frame.add(self.preview)
        vbox.pack_start(preview_frame, False)
        vbox.pack_end(self.call_button, False)
        hbox.add(output_frame)
        hbox.pack_start(vbox, padding=10)
        self.add(hbox)

    def _call_button_clicked(self, button):
        pass

class GtkLoopMixin:
    def run_main_loop(self):
        Gtk.main()

    def quit(self):
        Gtk.main_quit()

class BaseGtkCall:
    def __init__(self):
        self.window = CallWindow()
        self.window.connect('destroy', Gtk.main_quit)
        self.window.show_all()

    def add_preview_window(self):
        se = dbus.Interface(get_stream_engine(),
            'org.freedesktop.Telepathy.StreamEngine')
        se.AddPreviewWindow(self.window.preview.get_id())

        return False

    def add_output_window(self):
        se = dbus.Interface(get_stream_engine(),
            'org.freedesktop.Telepathy.StreamEngine')
        chan_path = self.channel.object_path
        se.SetOutputWindow(chan_path, 2, self.window.output.get_id())

        return False

class GtkOutgoingCall(GtkLoopMixin, BaseGtkCall, OutgoingCall):
    def __init__(self, account_file, contact):
        OutgoingCall.__init__(self, account_file, contact)
        BaseGtkCall.__init__(self)

    def members_changed_cb(self, message, added, removed, local_pending,
            remote_pending, actor, reason):
        OutgoingCall.members_changed_cb(self, message, added, removed,
            local_pending, remote_pending, actor, reason)

        if self.handle in added:
            GObject.timeout_add(5000, self.add_output_window)
            GObject.timeout_add(5000, self.add_preview_window)

class GtkIncomingCall(GtkLoopMixin, BaseGtkCall, IncomingCall):
    def __init__(self, account_file):
        IncomingCall.__init__(self, account_file)
        BaseGtkCall.__init__(self)

    def members_changed_cb(self, message, added, removed, local_pending,
            remote_pending, actor, reason):
        IncomingCall.members_changed_cb(self, message, added, removed,
            local_pending, remote_pending, actor, reason)

        if self.conn[CONN_INTERFACE].GetSelfHandle() in added:
            GObject.timeout_add(5000, self.add_output_window)
            GObject.timeout_add(5000, self.add_preview_window)

def usage():
    print("Usage:\n" \
            "Outcoming call to [contact]:\n" \
            "\tpython %s [account-file] [contact]\n" \
            "Accept incoming call:\n" \
            "\tpython %s [account-file]\n" \
            % (sys.argv[0], sys.argv[0]))

if __name__ == '__main__':
    args = sys.argv[1:]

    if len(args) == 2:
        contact = args[1]
        call = GtkOutgoingCall(args[0], args[1])
    elif len(args) == 1:
        call = GtkIncomingCall(args[0])
    else:
        usage()
        sys.exit(0)

    call.run()
