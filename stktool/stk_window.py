# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

import dbus
import dbus.mainloop.glib

from stktool.ofono_stk_agent import StkAgent, GoBack, Busy
from stktool.utils import print_property_changed, parse_stk_text
from stktool import ui

class StkWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connect("close-request", lambda _: self.cleanup_and_exit())
        self.set_title("SIM Toolkit")
        self.set_default_size(400, 600)

        ui.create_window_controls(self)

        # Create main layout
        self.toast_overlay, self.navigation_view = ui.create_main_window_layout()
        self.set_content(self.toast_overlay)

        # Create main page
        self.main_page = ui.create_non_swipeable_page("SIM Toolkit")

        # Create main page content
        (self.main_box, self.main_menu_title, self.scrolled_window,
         self.list_box, self.listbox, button_box,
         self.ok_button, self.cancel_button, self.status_banner) = ui.create_main_page_content()

        self.main_page.set_child(self.main_box)

        # Connect button events
        self.ok_button.connect("clicked", self.on_ok_clicked)
        self.cancel_button.connect("clicked", self.on_cancel_clicked)

        self.navigation_view.add(self.main_page)

        self.agent_path = "/appagent"
        self.agent = None
        self.stk = None
        self.vcm = None
        self.connection_state = "disconnected"

        self.show_loading_state("Initializing SIM Toolkit...")

        GLib.timeout_add(100, self.setup_stk)

    def cleanup_and_exit(self):
        try:
            if self.agent and self.stk:
                self.unregister_agent()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        exit(0)

    def show_loading_state(self, message: str):
        loading_page = ui.create_loading_status_page()
        loading_page.set_description(message)
        self.scrolled_window.set_child(loading_page)
        self.ok_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)

    def update_connection_status(self, state: str, message: str = ""):
        if state == "connected":
            self.status_banner.set_title("Connected to SIM Toolkit")
            self.status_banner.set_revealed(False)
            self.connection_state = "connected"
            self.cancel_button.set_sensitive(True)
        elif state == "error":
            self.status_banner.set_title(f"Connection Error: {message}")
            self.status_banner.set_revealed(True)
            self.connection_state = "error"
            self.cancel_button.set_sensitive(False)
        elif state == "disconnected":
            self.status_banner.set_title("Disconnected from SIM Toolkit")
            self.status_banner.set_revealed(True)
            self.connection_state = "disconnected"
            self.cancel_button.set_sensitive(False)

    def setup_stk(self):
        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SystemBus()
            manager = dbus.Interface(self.bus.get_object("org.ofono", "/"), "org.ofono.Manager")

            try:
                modems = manager.GetModems()
            except dbus.exceptions.DBusException as e:
                self.handle_connection_error("Failed to get modems", str(e))
                return False

            modem_found = False
            for path, properties in modems:
                modem_found = True
                if "org.ofono.SimToolkit" in properties["Interfaces"]:
                    self.stk = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.SimToolkit')
                if "org.ofono.VoiceCallManager" in properties["Interfaces"]:
                    self.vcm = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCallManager')

            if not modem_found:
                self.handle_connection_error("No modems found", "Please check your modem connection")
                return False

            if self.stk:
                try:
                    self.stk.connect_to_signal("PropertyChanged", self.property_changed)
                    self.properties = self.stk.GetProperties()
                    self.agent = StkAgent(self.bus, self.agent_path, self)
                    self.register_agent()
                    self.update_connection_status("connected")
                    print(f"oFono agent at path {self.agent_path} registered successfully")
                except dbus.exceptions.DBusException as e:
                    self.handle_connection_error("Failed to setup SIM Toolkit", str(e))
                    return False
            else:
                self.handle_connection_error("SIM Toolkit not available", "SIM Toolkit interface not found on any modem")
                return False

            if self.vcm:
                try:
                    self.vcm.connect_to_signal("CallAdded", self.agent.call_added)
                except Exception as e:
                    print(f"Warning: Failed to connect to CallAdded signal: {e}")

            self.update_ui()
            return False
        except Exception as e:
            self.handle_connection_error("Unexpected error during setup", str(e))
            return False

    def handle_connection_error(self, title: str, details: str):
        print(f"Connection error: {title} - {details}")

        # Update UI to show error state
        self.update_connection_status("error", title)

        # Show error status page
        error_page = ui.create_unavailable_status_page()
        error_page.set_title("Connection Error")
        error_page.set_description(f"Connection failed: {title}")
        self.scrolled_window.set_child(error_page)

        # Disable both buttons
        self.ok_button.set_sensitive(False)
        self.cancel_button.set_sensitive(False)

    def update_ui(self):
        if "MainMenuTitle" in self.properties:
            title_text = self.properties["MainMenuTitle"]
            parsed_title = parse_stk_text(title_text)

            if parsed_title.get('segments'):
                title_label = create_formatted_label(title_text, ["title-1"])
                title_label.set_halign(Gtk.Align.CENTER)
                title_label.set_valign(Gtk.Align.CENTER)

                self.main_menu_title.set_child(title_label)
            else:
                self.main_menu_title.set_child(None)
                self.main_menu_title.set_title(parsed_title.get('text', title_text))

        while (row := self.listbox.get_row_at_index(0)) is not None:
            self.listbox.remove(row)

        if "MainMenu" in self.properties and self.properties["MainMenu"]:
            self.scrolled_window.set_child(self.list_box)
            for _index, item in enumerate(self.properties["MainMenu"]):
                row = ui.setup_main_listbox_item(item[0])
                self.listbox.append(row)

            if self.connection_state == "connected":
                self.ok_button.set_sensitive(True)
                self.cancel_button.set_sensitive(True)
            else:
                self.ok_button.set_sensitive(False)
                self.cancel_button.set_sensitive(False)

            if self.listbox.get_row_at_index(0):
                self.listbox.select_row(self.listbox.get_row_at_index(0))
        else:
            status_page = ui.create_unavailable_status_page()
            self.scrolled_window.set_child(status_page)
            self.ok_button.set_sensitive(False)
            self.cancel_button.set_sensitive(False)
            self.cancel_button.set_label("Cancel")

    def property_changed(self, name, value):
        try:
            print_property_changed(name, value)
            self.properties[name] = value
            GLib.idle_add(self.update_ui)
        except Exception as e:
            print(f"Error handling property change: {e}")

    def on_ok_clicked(self, button):
        selected_row = self.listbox.get_selected_row()
        if not selected_row:
            ui.create_toast(self.toast_overlay, "Please select an item first.")
            return

        if self.connection_state != "connected":
            ui.create_toast(self.toast_overlay, "Not connected to SIM Toolkit")
            return

        try:
            button.set_sensitive(False)

            self.stk.SelectItem(selected_row.get_index(), self.agent_path)
        except dbus.exceptions.DBusException as e:
            button.set_sensitive(True)
            error_name = e.get_dbus_name() if hasattr(e, 'get_dbus_name') else str(type(e).__name__)

            if "InProgress" in error_name or "Busy" in error_name:
                ui.create_toast(self.toast_overlay, "Operation in progress. Please wait.")
            elif "NotSupported" in error_name:
                ui.create_toast(self.toast_overlay, "This operation is not supported")
            elif "Failed" in error_name:
                ui.create_toast(self.toast_overlay, "Operation failed. Please try again.")
            else:
                ui.create_toast(self.toast_overlay, f"Error: {str(e)}")

            print(f"D-Bus exception in on_ok_clicked: {e}")
        except Exception as e:
            button.set_sensitive(True)
            ui.create_toast(self.toast_overlay, "An unexpected error occurred")
            print(f"General exception in on_ok_clicked: {e}")
        finally:
            GLib.timeout_add(1000, lambda: button.set_sensitive(True))

    def on_cancel_clicked(self, button):
        if self.connection_state != "connected" or not self.stk:
            print("Cancel clicked but not connected to STK - ignoring")
            return
        try:
            self.unregister_agent()
            self.register_agent()
            self.navigation_view.pop_to_page(self.main_page)
        except Exception as e:
            print(f"Error in cancel operation: {e}")

    def register_agent(self):
        if not self.stk:
            print("Cannot register agent: STK interface not available")
            return

        try:
            self.stk.RegisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            error_msg = f"Failed to register agent: {str(e)}"
            ui.create_toast(self.toast_overlay, error_msg)
            print(error_msg)
            raise

    def unregister_agent(self):
        if not self.stk:
            print("Cannot unregister agent: STK interface not available")
            return

        try:
            self.stk.UnregisterAgent(self.agent_path)
        except dbus.exceptions.DBusException as e:
            error_msg = f"Failed to unregister agent: {str(e)}"
            print(error_msg)

    def show_display_text_popup(self, title, reply_func, error_func):
        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        parsed_title = parse_stk_text(title)
        dialog_title = parsed_title.get('text', title)

        dialog = ui.create_confirmation_dialog("Display Text", dialog_title, response_callback=on_response)
        dialog.present(self)

    def show_input_page(self, title, default, min_chars, reply_func, error_func, digits_only=False):
        parsed_title = parse_stk_text(title)
        page_title = parsed_title.get('text', title)

        page = ui.create_non_swipeable_page(page_title)

        (box, header, entry, button_box,
         ok_button, cancel_button, validation_label) = ui.create_input_page_content(
            title, default, digits_only)

        page.set_child(box)
        print(f"min chars is {min_chars}")
        try:
            min_chars_int = int(min_chars) if min_chars is not None else 0
        except (ValueError, TypeError):
            print("failed to convert min chars")
            min_chars_int = 0

        def on_ok_clicked(button):
            user_input = entry.get_text()

            if min_chars > 0 and len(user_input) < min_chars:
                ui.create_toast(self.toast_overlay, f"Input must be at least {min_chars} characters")
                return

            self.navigation_view.pop()
            GLib.idle_add(reply_func, user_input)

        def on_cancel_clicked(button):
            self.navigation_view.pop()
            GLib.idle_add(error_func, Busy())

        ok_button.connect("clicked", on_ok_clicked)
        cancel_button.connect("clicked", on_cancel_clicked)

        self.navigation_view.push(page)

    def show_selection_page(self, title, items, default, reply_callback, error_callback):
        parsed_title = parse_stk_text(title)
        page_title = parsed_title.get('text', title)

        page = ui.create_non_swipeable_page(page_title)

        (box, header, scrolled_window, listbox, button_box,
         ok_button, cancel_button) = ui.create_selection_page_content(title, items)

        page.set_child(box)

        if 0 <= default < len(items):
            listbox.select_row(listbox.get_row_at_index(default))
            item_text = items[default][0]
            parsed_item = parse_stk_text(item_text)
            header.set_description(parsed_item.get('text', item_text))

        def on_row_activated(listbox, row):
            listbox.select_row(row)
            item_text = items[row.get_index()][0]
            parsed_item = parse_stk_text(item_text)
            header.set_description(parsed_item.get('text', item_text))

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
            try:
                self.unregister_agent()
                self.register_agent()
            except Exception as e:
                print(f"Error refreshing agent: {e}")

        listbox.connect("row-activated", on_row_activated)
        ok_button.connect("clicked", on_ok_clicked)
        cancel_button.connect("clicked", on_cancel_clicked)

        self.navigation_view.push(page)

    def show_key_page(self, title, reply_func, error_func, digits_only=False):
        parsed_title = parse_stk_text(title)
        page_title = parsed_title.get('text', title)

        page = ui.create_non_swipeable_page(page_title)

        (box, title_label, clamp, entry, button_box,
         ok_button, back_button) = ui.create_key_page_content(title, digits_only)

        page.set_child(box)

        def on_text_changed(entry):
            text = entry.get_text()
            if text:
                # Auto-submit on single character
                if len(text) == 1:
                    if digits_only and not text.isdigit():
                        entry.set_text("")
                        return
                    GLib.timeout_add(500, lambda: on_ok_clicked(ok_button))

        def on_ok_clicked(button):
            key = entry.get_text()
            if not key:
                ui.create_toast(self.toast_overlay, "Please enter a key")
                return
            self.navigation_view.pop()
            GLib.idle_add(reply_func, key)

        def on_back_clicked(button):
            self.navigation_view.pop()
            GLib.idle_add(error_func, GoBack("User wishes to go back"))

        entry.connect("notify::text", lambda *args: on_text_changed(entry))
        ok_button.connect("clicked", on_ok_clicked)
        back_button.connect("clicked", on_back_clicked)

        GLib.idle_add(lambda: entry.grab_focus())

        self.navigation_view.push(page)

    def show_confirmation_popup(self, title, reply_func, error_func, info=None, url=None):
        def on_response(dialog, response):
            if response == "yes":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        parsed_title = parse_stk_text(title)
        dialog_title = parsed_title.get('text', title)

        parsed_info = None
        if info:
            parsed_info = parse_stk_text(info)
            info = parsed_info.get('text', info)

        dialog = ui.create_confirmation_dialog(dialog_title, info, url, on_response)
        dialog.present(self)

    def show_tone_page(self, tone, text):
        def on_response(dialog, response):
            # TODO: do something
            pass

        parsed_text = parse_stk_text(text)
        dialog_text = parsed_text.get('text', text)

        dialog = ui.create_tone_dialog(dialog_text, tone, on_response)
        dialog.present(self)

    def show_loop_tone_page(self, tone, text, reply_func, error_func):
        def on_response(dialog, response):
            if response == "wait":
                GLib.idle_add(reply_func, True)
            else:
                GLib.idle_add(reply_func, False)

        parsed_text = parse_stk_text(text)
        dialog_text = parsed_text.get('text', text)

        dialog = ui.create_loop_tone_dialog(dialog_text, tone, on_response)
        dialog.present(self)

    def show_action_info_popup(self, text):
        parsed_text = parse_stk_text(text)
        dialog_text = parsed_text.get('text', text)

        dialog = ui.create_action_info_dialog(dialog_text)
        dialog.present(self)

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

        if self.connection_state == "connected":
            self.ok_button.set_sensitive(True)
            self.cancel_button.set_sensitive(True)
        else:
            self.ok_button.set_sensitive(False)
            self.cancel_button.set_sensitive(False)
