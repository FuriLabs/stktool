# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import gi
from gi.repository import GLib

import dbus
import dbus.service

from stktool.utils import print_method_call

# the skel implementation here comes from test-stk-menu but all the logic is stripped out and moved to StkWindow to handle and draw
class GoBack(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.GoBack"

class EndSession(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.EndSession"

class Busy(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.Busy"

class StkAgent(dbus.service.Object):
    def __init__(self, bus, path, window):
        super().__init__(bus, path)
        self.window = window
        self.timeout_id = 0
        self.timeout_reply_handler = None
        self.active_operations = 0

    def timeout_callback(self):
        self.timeout_id = 0
        if self.timeout_reply_handler:
            try:
                self.timeout_reply_handler()
            except Exception as e:
                print(f"Error in timeout callback: {e}")
        return False

    def call_added(self, path, properties):
        print(f"Call added: {path}")
        # Cancel any pending STK operations when a call comes in
        if self.timeout_id > 0:
            GLib.source_remove(self.timeout_id)
            self.timeout_callback()

    def _handle_method_error(self, method_name, error, error_callback=None):
        error_msg = f"Error in {method_name}: {str(error)}"
        print(error_msg)

        if error_callback:
            try:
                if "timeout" in str(error).lower():
                    error_callback(Busy("Operation timed out"))
                else:
                    error_callback(Busy(str(error)))
            except Exception as e:
                print(f"Error calling error callback: {e}")

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="", out_signature="")
    def Release(self):
        print("STK Agent Released")
        self.active_operations = 0
        if self.timeout_id > 0:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = 0

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sya(sy)n", out_signature="y",
                         async_callbacks=("reply_callback", "error_callback"))
    def RequestSelection(self, title, icon, items, default, reply_callback, error_callback):
        try:
            print_method_call("RequestSelection",
                              title=title,
                              icon=icon,
                              items=items,
                              default=default)

            self.active_operations += 1

            # Validate inputs
            if not items:
                error_callback(Busy("No menu items available"))
                return

            if default < 0 or default >= len(items):
                default = 0

            self.window.show_selection_page(title, items, default, reply_callback, error_callback)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestSelection", e, error_callback)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="syb", out_signature="",
                         async_callbacks=("reply_func", "error_func"))
    def DisplayText(self, title, icon, urgent, reply_func, error_func):
        try:
            print_method_call("DisplayText",
                              title=title,
                              icon=icon,
                              urgent=urgent)

            self.active_operations += 1

            # Validate input
            if not title or not title.strip():
                title = "No message provided"

            self.window.show_display_text_popup(title, reply_func, error_func)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("DisplayText", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sysyyb", out_signature="s",
                         async_callbacks=("reply_func", "error_func"))
    def RequestInput(self, title, icon, default, min_chars, max_chars, hide_typing, reply_func, error_func):
        try:
            print_method_call("RequestInput",
                              title=title,
                              icon=icon,
                              default=default,
                              min_chars=min_chars,
                              max_chars=max_chars,
                              hide_typing=hide_typing)

            self.active_operations += 1

            # Validate and sanitize inputs
            if not title or not title.strip():
                title = "Enter text"

            if not default:
                default = ""

            self.window.show_input_page(title, default, min_chars, reply_func, error_func)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestInput", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sysyyb", out_signature="s",
                         async_callbacks=("reply_func", "error_func"))
    def RequestDigits(self, title, icon, default, min_chars, max_chars, hide_typing, reply_func, error_func):
        try:
            print_method_call("RequestDigits",
                              title=title,
                              icon=icon,
                              default=default,
                              min_chars=min_chars,
                              max_chars=max_chars,
                              hide_typing=hide_typing)

            self.active_operations += 1

            # Validate and sanitize inputs
            if not title or not title.strip():
                title = "Enter digits"

            # Ensure default contains only digits
            if default and not str(default).isdigit():
                default = ""
            else:
                default = str(default) if default else ""

            self.window.show_input_page(title, default, min_chars, reply_func, error_func, digits_only=True)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestDigits", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="s",
                         async_callbacks=("reply_func", "error_func"))
    def RequestKey(self, title, icon, reply_func, error_func):
        try:
            print_method_call("RequestKey",
                              title=title,
                              icon=icon)

            self.active_operations += 1

            if not title or not title.strip():
                title = "Press any key"

            self.window.show_key_page(title, reply_func, error_func)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestKey", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="s",
                         async_callbacks=("reply_func", "error_func"))
    def RequestDigit(self, title, icon, reply_func, error_func):
        try:
            print_method_call("RequestDigit",
                              title=title,
                              icon=icon)

            self.active_operations += 1

            if not title or not title.strip():
                title = "Press any digit"

            self.window.show_key_page(title, reply_func, error_func, digits_only=True)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestDigit", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="b",
                         async_callbacks=("reply_func", "error_func"))
    def RequestConfirmation(self, title, icon, reply_func, error_func):
        try:
            print_method_call("RequestConfirmation",
                              title=title,
                              icon=icon)

            self.active_operations += 1

            if not title or not title.strip():
                title = "Confirm action"

            self.window.show_confirmation_popup(title, reply_func, error_func)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("RequestConfirmation", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="b",
                         async_callbacks=("reply_func", "error_func"))
    def ConfirmCallSetup(self, info, icon, reply_func, error_func):
        try:
            print_method_call("ConfirmCallSetup",
                              info=info,
                              icon=icon)

            self.active_operations += 1

            if not info or not info.strip():
                info = "Unknown number"

            self.window.show_confirmation_popup("Confirm Call Setup", reply_func, error_func, info=info)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("ConfirmCallSetup", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sys", out_signature="b",
                         async_callbacks=("reply_func", "error_func"))
    def ConfirmLaunchBrowser(self, info, icon, url, reply_func, error_func):
        try:
            print_method_call("ConfirmLaunchBrowser",
                              info=info,
                              icon=icon,
                              url=url)

            self.active_operations += 1

            if not url or not url.strip():
                url = "Unknown URL"

            self.window.show_confirmation_popup("Confirm Launch Browser", reply_func, error_func,
                                                info=info, url=url)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("ConfirmLaunchBrowser", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="", out_signature="")
    def Cancel(self):
        try:
            print("\nCancel operation received")
            self.active_operations = 0

            # Cancel any pending timeouts
            if self.timeout_id > 0:
                GLib.source_remove(self.timeout_id)
                self.timeout_id = 0

            # Return to main page
            GLib.idle_add(self.window.pop_to_main_page)
        except Exception as e:
            print(f"Error in Cancel: {e}")

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="ssy", out_signature="")
    def PlayTone(self, tone, text, icon):
        try:
            print_method_call("PlayTone",
                              tone=tone,
                              text=text,
                              icon=icon)

            if not text or not text.strip():
                text = "Playing tone"

            self.window.show_tone_page(tone, text)
        except Exception as e:
            self._handle_method_error("PlayTone", e)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="ssy", out_signature="",
                         async_callbacks=("reply_func", "error_func"))
    def LoopTone(self, tone, text, icon, reply_func, error_func):
        try:
            print_method_call("LoopTone",
                              tone=tone,
                              text=text,
                              icon=icon)

            self.active_operations += 1

            if not text or not text.strip():
                text = "Playing tone"

            self.window.show_loop_tone_page(tone, text, reply_func, error_func)
        except Exception as e:
            self.active_operations = max(0, self.active_operations - 1)
            self._handle_method_error("LoopTone", e, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="")
    def DisplayActionInformation(self, text, icon):
        try:
            print_method_call("DisplayActionInformation",
                              text=text,
                              icon=icon)

            if not text or not text.strip():
                text = "No information provided"

            self.window.show_action_info_popup(text)
        except Exception as e:
            self._handle_method_error("DisplayActionInformation", e)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="")
    def DisplayAction(self, text, icon):
        try:
            print_method_call("DisplayAction",
                              text=text,
                              icon=icon)

            if not text or not text.strip():
                text = "Action in progress"

            self.window.show_action_page(text)
        except Exception as e:
            self._handle_method_error("DisplayAction", e)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sy", out_signature="b")
    def ConfirmOpenChannel(self, info, icon):
        try:
            print_method_call("ConfirmOpenChannel",
                              info=info,
                              icon=icon)

            if not info or not info.strip():
                info = "Open network channel"

            return self.window.show_confirm_open_channel_page(info)
        except Exception as e:
            self._handle_method_error("ConfirmOpenChannel", e)
            return False
