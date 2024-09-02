# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2024 Bardia Moshiri <bardia@furilabs.com>

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango

import dbus
import dbus.mainloop.glib

from stktool.ofono_stk_agent import StkAgent, GoBack, EndSession, Busy

class StkWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect("close-request", lambda _: exit(0))
        self.set_title("SIM Toolkit")
        self.set_default_size(400, 600)

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        self.navigation_view = Adw.NavigationView()
        self.toast_overlay.set_child(self.navigation_view)

        self.main_page = Adw.NavigationPage(title="SIM Toolkit")
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_page.set_child(self.main_box)

        self.main_menu_title = Adw.StatusPage()
        self.main_box.append(self.main_menu_title)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_min_content_height(400)
        self.scrolled_window.set_vexpand(True)
        self.main_box.append(self.scrolled_window)

        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.scrolled_window.set_child(self.list_box)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.add_css_class("boxed-list")
        self.list_box.append(self.listbox)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_margin_top(12)
        button_box.set_margin_bottom(24)
        button_box.set_halign(Gtk.Align.CENTER)
        self.main_box.append(button_box)

        self.ok_button = Gtk.Button(label="OK")
        self.ok_button.connect("clicked", self.on_ok_clicked)
        button_box.append(self.ok_button)

        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        button_box.append(self.cancel_button)

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

        self.stk.connect_to_signal("PropertyChanged", self.property_changed)
        self.properties = self.stk.GetProperties()

        self.agent = StkAgent(self.bus, self.agent_path, self)
        self.register_agent()

        try:
            self.vcm.connect_to_signal("CallAdded", self.agent.call_added)
        except:
            print("Failed to connect to signal CallAdded") # i... don't know?

        self.update_ui()

    def update_ui(self):
        if "MainMenuTitle" in self.properties:
            self.main_menu_title.set_title(self.properties["MainMenuTitle"])

        while (row := self.listbox.get_row_at_index(0)) is not None:
            self.listbox.remove(row)

        if "MainMenu" in self.properties and self.properties["MainMenu"]:
            self.scrolled_window.set_child(self.list_box)
            for index, item in enumerate(self.properties["MainMenu"]):
                row = Adw.ActionRow(title=item[0])
                self.listbox.append(row)

            self.ok_button.set_sensitive(True)
            self.cancel_button.set_sensitive(True)
            if self.listbox.get_row_at_index(0):
                self.listbox.select_row(self.listbox.get_row_at_index(0))
        else:
            status_page = Adw.StatusPage()
            status_page.set_icon_name("dialog-warning-symbolic")
            status_page.set_title("SIM Toolkit Unavailable")
            status_page.set_description("SIM Toolkit is not available right now")
            self.scrolled_window.set_child(status_page)

            self.ok_button.set_sensitive(False)
            self.cancel_button.set_sensitive(False)

    def property_changed(self, name, value):
        # print(f"property changed: name: {name}, value: {value}")
        self.properties[name] = value
        GLib.idle_add(self.update_ui)

    def on_ok_clicked(self, button):
        selected_row = self.listbox.get_selected_row()
        if selected_row:
            # print(f"Selected item index: {selected_row.get_index()}")
            try:
                self.stk.SelectItem(selected_row.get_index(), "/appagent")
            except dbus.exceptions.DBusException as e:
                self.show_toast("Operation in progress. Please wait.")
                print(f"on_ok_clicked: dbus exception: {e}")
            except Exception as e:
                self.show_toast("{e}")
                printf(f"on_ok_clicked: general exception: {e}")
        else:
            self.show_toast("Please select an item first.")

    def show_toast(self, message, duration=3):
        toast = Adw.Toast(title=message)
        self.toast_overlay.add_toast(toast)

        def dismiss_toast():
            toast.dismiss()
            return False

        GLib.timeout_add_seconds(duration, dismiss_toast)

    def register_agent(self):
        try:
            self.stk.RegisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            self.show_toast(f"Failed to register agent: {str(e)}")
            print(f"Failed to register agent: {str(e)}")

    def unregister_agent(self):
        try:
            self.stk.UnregisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            self.show_toast(f"Failed to unregister agent: {str(e)}")
            print(f"Failed to unregister agent: {str(e)}")

    # this is cancel in the main menu
    def on_cancel_clicked(self, button):
        self.unregister_agent()
        self.register_agent()
        self.navigation_view.pop_to_page(self.main_page)

    def show_display_text_popup(self, title, reply_func, error_func):
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)

        dialog.add_response("no", ("No"))

        dialog.add_response("yes", ("Yes"))
        dialog.set_default_response("no")
        dialog.set_close_response("no")

        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog.connect("response", on_response)
        dialog.present()

    def show_input_page(self, title, default, reply_func, error_func, digits_only=False):
        page = Adw.NavigationPage(title=title)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_child(box)

        title_label = Gtk.Label(label=title)
        title_label.set_wrap(True)
        title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title_label.set_max_width_chars(30)
        title_label.add_css_class("title-4")
        title_label.set_margin_top(12)
        title_label.set_margin_bottom(12)
        title_label.set_margin_start(12)
        title_label.set_margin_end(12)

        clamp = Adw.Clamp()
        clamp.set_child(title_label)
        box.append(clamp)

        entry = Adw.EntryRow(title="Input")
        entry.set_text(default)

        if digits_only:
            entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        box.append(entry)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)

        ok_button = Gtk.Button(label="OK")
        cancel_button = Gtk.Button(label="Cancel")
        button_box.append(ok_button)
        button_box.append(cancel_button)

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
        page = Adw.NavigationPage(title=title)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_child(box)

        status_page = Adw.StatusPage()
        status_page.set_title(title)
        box.append(status_page)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(400)
        scrolled_window.set_vexpand(True)
        box.append(scrolled_window)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.add_css_class("boxed-list")
        scrolled_window.set_child(listbox)

        for i, item in enumerate(items):
            row = Adw.ActionRow(title=item[0])
            listbox.append(row)

        if 0 <= default < len(items):
            listbox.select_row(listbox.get_row_at_index(default))
            status_page.set_description(items[default][0])

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)
        button_box.set_margin_bottom(24)
        box.append(button_box)

        ok_button = Gtk.Button(label="OK")
        cancel_button = Gtk.Button(label="Cancel")
        button_box.append(ok_button)
        button_box.append(cancel_button)

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
                self.show_toast("Please select an option")

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
        page = Adw.NavigationPage(title=title)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_child(box)

        title_label = Gtk.Label(label=title)
        title_label.set_wrap(True)
        title_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        title_label.set_max_width_chars(30)
        title_label.add_css_class("title-4")
        title_label.set_margin_top(12)
        title_label.set_margin_bottom(12)
        title_label.set_margin_start(12)
        title_label.set_margin_end(12)

        clamp = Adw.Clamp()
        clamp.set_child(title_label)
        box.append(clamp)

        entry = Adw.EntryRow(title="Key")
        if digits_only:
            entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        box.append(entry)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)

        ok_button = Gtk.Button(label="OK")
        back_button = Gtk.Button(label="Back")
        button_box.append(ok_button)
        button_box.append(back_button)

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
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)

        body_text = ""
        if info:
            body_text += info
        if url:
            if body_text:
                body_text += "\n\n"
            body_text += f"URL: {url}"

        if body_text:
            dialog.set_body(body_text)

        dialog.add_response("no", ("No"))

        dialog.add_response("yes", ("Yes"))
        dialog.set_default_response("no")
        dialog.set_close_response("no")

        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog.connect("response", on_response)
        dialog.present()

    def show_tone_page(self, tone, text):
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(text)

        if tone:
            dialog.set_body(tone)

        dialog.add_response("end", ("End Tone"))
        dialog.set_default_response("end")
        dialog.set_close_response("end")

        def on_response(dialog, response):
            pass

        dialog.connect("response", on_response)
        dialog.present()

    def show_loop_tone_page(self, tone, text, reply_func, error_func):
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(text)

        if tone:
            dialog.set_body(tone)

        dialog.add_response("wait", ("Wait"))

        dialog.add_response("end", ("End Tone"))
        dialog.set_default_response("end")
        dialog.set_close_response("end")

        def on_response(dialog, response):
            if response == "wait":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        dialog.connect("response", on_response)
        dialog.present()

    def show_action_info_popup(self, text):
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(text)

        dialog.add_response("ok", ("OK"))
        dialog.set_default_response("ok")
        dialog.set_close_response("ok")

        dialog.present()

    def show_action_page(self, text):
        page = Adw.NavigationPage(title="Action")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_child(box)

        status_page = Adw.StatusPage(
            title="Action",
            description=f"Text: {text}"
        )
        box.append(status_page)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)

        ok_button = Gtk.Button(label="OK")
        button_box.append(ok_button)

        def on_ok_clicked(button):
            self.navigation_view.pop()

        ok_button.connect("clicked", on_ok_clicked)

        self.navigation_view.push(page)

    def show_confirm_open_channel_page(self, info):
        page = Adw.NavigationPage(title="Confirm Open Channel")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_child(box)

        status_page = Adw.StatusPage(
            title="Confirm Open Channel",
            description=f"Information: {info}"
        )
        box.append(status_page)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)

        yes_button = Gtk.Button(label="Yes")
        no_button = Gtk.Button(label="No")
        button_box.append(yes_button)
        button_box.append(no_button)

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
