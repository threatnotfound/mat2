#!/usr/bin/env python3

import gi
gi.require_version('Nautilus', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Nautilus, GObject, Gtk, Gio
from urllib.parse import unquote
import mimetypes

import os

from libmat2 import parser_factory

class Mat2Wrapper():
    def __init__(self, filepath):
        self.filepath = filepath

class StatusWindow(Gtk.Window):
    def __init__(self, items):
        self.window = Gtk.Window()
        self.window.set_border_width(10)

        self.items = items
        self.confirm_window()

    def confirm_window(self):
        # Header bar
        hb = Gtk.HeaderBar()
        self.window.set_titlebar(hb)
        hb.props.title = "Remove metadata"

        cancel = Gtk.Button("Cancel")
        cancel.connect("clicked", self.cancel_btn)
        hb.pack_start(cancel)

        self.remove = Gtk.Button("Remove")
        self.remove.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION);
        self.remove.connect("clicked", self.remove_btn)
        hb.pack_end(self.remove)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(self.main_box)

        # List of files to clean
        listbox = Gtk.ListBox()
        self.main_box.pack_start(listbox, True, True, 0)
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        for i in self.items:
            p, mtype = parser_factory.get_parser(i)

            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row.add(hbox)

            icon = Gio.content_type_get_icon ('text/plain' if not mtype else mtype)
            select_image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            hbox.pack_start(select_image, False, False, 0)

            image = Gtk.Image()
            image.set_from_stock(Gtk.STOCK_NO if not p else Gtk.STOCK_YES, Gtk.IconSize.BUTTON)
            hbox.pack_start(image, False, False, 0)

            label = Gtk.Label(os.path.basename(i))
            hbox.pack_start(label, True, False, 0)

            listbox.add(row)
        listbox.show_all()

        # Options
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box.pack_start(separator, True, True, 5)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.main_box.pack_start(hbox, True, True, 0)
        label = Gtk.Label(xalign=0)
        label.set_markup("Lightweight mode (only remove <i>some</i> metadata)")
        hbox.pack_start(label, False, True, 0)
        hbox.pack_start(Gtk.Switch(), False, True, 0)

        self.window.show_all()

    def error_window(self, items):
        self.window.remove(self.main_box)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(box)

        # Disclaimer
        box.pack_start(Gtk.Label("Could not remove metadata from the following items:",
                                 xalign=0), True, True, 0)

        # List of failed files
        listbox = Gtk.ListBox()
        box.pack_start(listbox, True, True, 0)
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        for i in items:
            listbox.add(Gtk.Label(os.path.basename(i), xalign=0))
        listbox.show_all()

        self.window.show_all()
        self.remove.hide()

    def cancel_btn(self, button):
        self.window.close()

    def remove_btn(self, button):
        failed = []
        for i in self.items:
            p, mtype = parser_factory.get_parser(i)
            if p is not None and p.remove_all():
                continue
            failed.append(i)

        # Everything went the right way, exit
        if not len(failed):
            self.window.close()

        self.error_window(failed)

class ColumnExtension(GObject.GObject, Nautilus.MenuProvider):
    def __validate(self, file):
        if file.get_uri_scheme() != "file" or file.is_directory():
            return False
        if not file.can_write():
            return False
        return True

    def menu_activate_cb(self, menu, files):
        items = list(map(lambda x: unquote(x.get_uri()[7:]), files))
        StatusWindow(items)

    def get_background_items(self, window, file):
        """ https://bugzilla.gnome.org/show_bug.cgi?id=784278 """
        return None

    def get_file_items(self, window, files):
        # Do not show the menu item if not a single file has a chance to be
        # processed by mat2.
        if not any(map(self.__validate, files)):
            return

        item = Nautilus.MenuItem(
            name="MAT2::Remove_metadata",
            label="Remove metadata",
            tip="Remove metadata"
        )
        item.connect('activate', self.menu_activate_cb, files)

        return [item]
