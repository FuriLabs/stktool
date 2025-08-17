# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

import dbus
import dbus.mainloop.glib

from stktool.ofono_stk_agent import StkAgent, GoBack, EndSession, Busy
from stktool.utils import print_property_changed
from stktool import ui

class StkWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect("close-request", lambda _: exit(0))
        self.set_title("SIM Toolkit")
        self.set_default_size(400, 600)

        # Create main layout
        self.toast_overlay, self.navigation_view = ui.create_main_window_layout()
        self.set_content(self.toast_overlay)

        # Create main page
        self.main_page = ui.create_non_swipeable_page("SIM Toolkit")

        # Create main page content
        (self.main_box, self.main_menu_title, self.scrolled_window,
         self.list_box, self.listbox, button_box,
         self.ok_button, self.cancel_button) = ui.create_main_page_content()

        self.main_page.set_child(self.main_box)

        # Connect button events
        self.ok_button.connect("clicked", self.on_ok_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)

        self.navigation_view.add(self.main_page)

        self.agent_path = "/appagent"
        self.agent = None
        self.stk = None
        self.vcm = None

        self.setup_stk()

    def setup_stk(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        manager = dbus.Interface(self.bus.get_object("org.ofono", "/"), "org.ofono.Manager")
        modems = manager.GetModems()
        for path, properties in modems:
            if "org.ofono.SimToolkit" in properties["Interfaces"]:
                self.stk = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.SimToolkit')
            if "org.ofono.VoiceCallManager" in properties["Interfaces"]:
                self.vcm = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCallManager')

        if self.stk:
            self.stk.connect_to_signal("PropertyChanged", self.property_changed)
            self.properties = self.stk.GetProperties()
            self.agent = StkAgent(self.bus, self.agent_path, self)
            self.register_agent()
            print(f"oFono agent at path {self.agent_path} registered successfully")
        else:
            self.properties = []

        if self.vcm:
            try:
                self.vcm.connect_to_signal("CallAdded", self.agent.call_added)
            except:
                print("Failed to connect to signal CallAdded")

        self.update_ui()

    def update_ui(self):
        if "MainMenuTitle" in self.properties:
            self.main_menu_title.set_title(self.properties["MainMenuTitle"])

        while (row := self.listbox.get_row_at_index(0)) is not None:
            self.listbox.remove(row)

        if "MainMenu" in self.properties and self.properties["MainMenu"]:
            self.scrolled_window.set_child(self.list_box)
            for index, item in enumerate(self.properties["MainMenu"]):
                row = ui.setup_main_listbox_item(item[0])
                self.listbox.append(row)

            self.ok_button.set_sensitive(True)
            self.cancel_button.set_sensitive(True)
            if self.listbox.get_row_at_index(0):
                self.listbox.select_row(self.listbox.get_row_at_index(0))
        else:
            status_page = ui.create_unavailable_status_page()
            self.scrolled_window.set_child(status_page)
            self.ok_button.set_sensitive(False)
            self.cancel_button.set_sensitive(False)

    def property_changed(self, name, value):
        print_property_changed(name, value)
        self.properties[name] = value
        GLib.idle_add(self.update_ui)

    def on_ok_clicked(self, button):
        selected_row = self.listbox.get_selected_row()
        if selected_row:
            try:
                self.stk.SelectItem(selected_row.get_index(), "/appagent")
            except dbus.exceptions.DBusException as e:
                ui.create_toast(self.toast_overlay, "Operation in progress. Please wait.")
                print(f"on_ok_clicked: dbus exception: {e}")
            except Exception as e:
                ui.create_toast(self.toast_overlay, f"{e}")
                print(f"on_ok_clicked: general exception: {e}")
        else:
            ui.create_toast(self.toast_overlay, "Please select an item first.")

    def register_agent(self):
        try:
            self.stk.RegisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            ui.create_toast(self.toast_overlay, f"Failed to register agent: {str(e)}")
            print(f"Failed to register agent: {str(e)}")

    def unregister_agent(self):
        try:
            self.stk.UnregisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            ui.create_toast(self.toast_overlay, f"Failed to unregister agent: {str(e)}")
            print(f"Failed to unregister agent: {str(e)}")

    def on_cancel_clicked(self, button):
        self.unregister_agent()
        self.register_agent()
        self.navigation_view.pop_to_page(self.main_page)

    def show_display_text_popup(self, title, reply_func, error_func):
        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog = ui.create_display_text_dialog(self, title, on_response)
        dialog.present()

    def show_input_page(self, title, default, reply_func, error_func, digits_only=False):
        page = ui.create_non_swipeable_page(title)

        (box, title_label, clamp, entry, button_box,
         ok_button, cancel_button) = ui.create_input_page_content(title, default, digits_only)

        page.set_child(box)

        def on_ok_clicked(button):
            user_input = entry.get_text()
            self.navigation_view.pop()
            GLib.idle_add(reply_func, user_input)

        def on_cancel_clicked(button):
            self.navigation_view.pop()
            GLib.idle_add(error_func, Busy())

        ok_button.connect("clicked", on_ok_clicked)
        cancel_button.connect("clicked", on_cancel_clicked)

        self.navigation_view.push(page)

    def show_selection_page(self, title, items, default, reply_callback, error_callback):
        page = ui.create_non_swipeable_page(title)

        (box, status_page, scrolled_window, listbox, button_box,
         ok_button, cancel_button) = ui.create_selection_page_content(title, items)

        page.set_child(box)

        if 0 <= default < len(items):
            listbox.select_row(listbox.get_row_at_index(default))
            status_page.set_description(items[default][0])

        def on_row_activated(listbox, row):
            listbox.select_row(row)
            status_page.set_description(items[row.get_index()][0])

        def on_ok_clicked(button):
            selected_row = listbox.get_selected_row()
            if selected_row:
                selection = selected_row.get_index()
                self.navigation_view.pop()
                GLib.idle_add(reply_callback, dbus.Byte(selection))
            else:
                ui.create_toast(self.toast_overlay, "Please select an option")

        def on_cancel_clicked(button):
            self.navigation_view.pop()
            GLib.idle_add(reply_callback, dbus.Byte(255))
            self.unregister_agent()
            self.register_agent()

        listbox.connect("row-activated", on_row_activated)
        ok_button.connect("clicked", on_ok_clicked)
        cancel_button.connect("clicked", on_cancel_clicked)

        self.navigation_view.push(page)

    def show_key_page(self, title, reply_func, error_func, digits_only=False):
        page = ui.create_non_swipeable_page(title)

        (box, title_label, clamp, entry, button_box,
         ok_button, back_button) = ui.create_key_page_content(title, digits_only)

        page.set_child(box)

        def on_ok_clicked(button):
            key = entry.get_text()
            self.navigation_view.pop()
            GLib.idle_add(reply_func, key)

        def on_back_clicked(button):
            self.navigation_view.pop()
            GLib.idle_add(error_func, GoBack("User wishes to go back"))

        ok_button.connect("clicked", on_ok_clicked)
        back_button.connect("clicked", on_back_clicked)

        self.navigation_view.push(page)

    def show_confirmation_popup(self, title, reply_func, error_func, info=None, url=None):
        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog = ui.create_confirmation_dialog(self, title, info, url, on_response)
        dialog.present()

    def show_tone_page(self, tone, text):
        def on_response(dialog, response):
            pass

        dialog = ui.create_tone_dialog(self, text, tone, on_response)
        dialog.present()

    def show_loop_tone_page(self, tone, text, reply_func, error_func):
        def on_response(dialog, response):
            if response == "wait":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog = ui.create_loop_tone_dialog(self, text, tone, on_response)
        dialog.present()

    def show_action_info_popup(self, text):
        dialog = ui.create_action_info_dialog(self, text)
        dialog.present()

    def show_action_page(self, text):
        page = ui.create_non_swipeable_page("Action")

        (box, status_page, button_box, ok_button) = ui.create_action_page_content(text)

        page.set_child(box)

        def on_ok_clicked(button):
            self.navigation_view.pop()

        ok_button.connect("clicked", on_ok_clicked)
        self.navigation_view.push(page)

    def show_confirm_open_channel_page(self, info):
        page = ui.create_non_swipeable_page("Confirm Open Channel")

        (box, status_page, button_box, yes_button, no_button) = ui.create_confirm_open_channel_page_content(info)

        page.set_child(box)

        result = [False]

        def on_yes_clicked(button):
            result[0] = True
            self.navigation_view.pop()

        def on_no_clicked(button):
            result[0] = False
            self.navigation_view.pop()

        yes_button.connect("clicked", on_yes_clicked)
        no_button.connect("clicked", on_no_clicked)

        self.navigation_view.push(page)

        while self.navigation_view.get_visible_page() == page:
            Gtk.main_iteration()

        return result[0]

    def pop_to_main_page(self):
        while self.navigation_view.get_visible_page() != self.main_page:
            self.navigation_view.pop()
