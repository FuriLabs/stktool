import gi
from gi.repository import GLib

import dbus
import dbus.service

# the skel implementation here comes from test-stk-menu but all the logic is stripped out and moved to StkWindow to handle and draw
class GoBack(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.GoBack"

class EndSession(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.EndSession"

class Busy(dbus.DBusException):
    _dbus_error_name = "org.ofono.Error.Busy"

class StkAgent(dbus.service.Object):
    timeout_id = 0
    timeout_reply_handler = None

    def __init__(self, bus, path, window):
        super().__init__(bus, path)
        self.window = window

    def timeout_callback(self):
        self.timeout_id = 0
        self.timeout_reply_handler()
        return False

    def call_added(self, path, properties):
        # print("call added %s" % (path))
        # so basically if there is a call operation going on we need to hold as stk won't answer, do something with this
        if (self.timeout_id > 0):
            GLib.source_remove(self.timeout_id)
            self.timeout_callback()

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="", out_signature="")
    def Release(self):
        print("Release")

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="sya(sy)n", out_signature="y",
                         async_callbacks=("reply_callback", "error_callback"))
    def RequestSelection(self, title, icon, items, default, reply_callback, error_callback):
        # print(f"RequestSelection: title: {title}, icon: {icon}, items: {items}, default: {default}")
        self.window.show_selection_page(title, items, default, reply_callback, error_callback)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                         in_signature="syb", out_signature="",
                         async_callbacks=("reply_func", "error_func"))
    def DisplayText(self, title, icon, urgent, reply_func, error_func):
        # print(f"DisplayText: title: {title}, icon: {icon}, urgent: {urgent}")
        self.window.show_display_text_popup(title, reply_func, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sysyyb", out_signature="s",
                async_callbacks=("reply_func", "error_func"))
    def RequestInput(self, title, icon, default, min_chars, max_chars, hide_typing, reply_func, error_func):
        # print(f"RequestInput: title: {title}, icon: {icon}, default: {default}, min_chars: {min_chars}, max_chars: {max_chars}, hide_typing: {hide_typing}")
        self.window.show_input_page(title, default, min_chars, reply_func, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sysyyb", out_signature="s",
                async_callbacks=("reply_func", "error_func"))
    def RequestDigits(self, title, icon, default, min_chars, max_chars, hide_typing, reply_func, error_func):
        # print(f"RequestDigits: title: {title}, icon: {icon}, default: {default}, min_chars: {min_chars}, max_chars: {max_chars}, hide_typing: {hide_typing}")
        self.window.show_input_page(title, default, reply_func, error_func, digits_only=True)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sy", out_signature="s",
                async_callbacks=("reply_func", "error_func"))
    def RequestKey(self, title, icon, reply_func, error_func):
        # print(f"RequestKey: title: {title}, icon: {icon}")
        self.window.show_key_page(title, reply_func, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sy", out_signature="s",
                async_callbacks=("reply_func", "error_func"))
    def RequestDigit(self, title, icon, reply_func, error_func):
        # print(f"RequestDigit: title: {title}, icon: {icon}")
        self.window.show_key_page(title, reply_func, error_func, digits_only=True)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sy", out_signature="b",
                async_callbacks=("reply_func", "error_func"))
    def RequestConfirmation(self, title, icon, reply_func, error_func):
        # print(f"RequestConfirmation: title: {title}, icon: {icon}")
        self.window.show_confirmation_popup(title, reply_func, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sy", out_signature="b",
                async_callbacks=("reply_func", "error_func"))
    def ConfirmCallSetup(self, info, icon, reply_func, error_func):
        # print(f"ConfirmCallSetup: info: {info}, icon: {icon}")
        self.window.show_confirmation_popup("Confirm Call Setup", reply_func, error_func, info=info)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                in_signature="sys", out_signature="b",
                async_callbacks=("reply_func", "error_func"))
    def ConfirmLaunchBrowser(self, info, icon, url, reply_func, error_func):
        # print(f"ConfirmLaunchBrowser: info: {info}, icon: {icon}, url: {url}")
        self.window.show_confirmation_popup("Confirm Launch Browser", reply_func, error_func, info=info, url=url)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="", out_signature="")
    def Cancel(self):
        # print("Cancel")
        self.window.pop_to_main_page()

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="ssy", out_signature="")
    def PlayTone(self, tone, text, icon):
        # print(f"PlayTone: tone: {tone}, text: {text}, icon: {icon}")
        self.window.show_tone_page(tone, text)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="ssy", out_signature="",
                    async_callbacks=("reply_func", "error_func"))
    def LoopTone(self, tone, text, icon, reply_func, error_func):
        # print(f"LoopTone: tone: {tone}, text: {text}, icon: {icon}")
        self.window.show_loop_tone_page(tone, text, reply_func, error_func)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="sy", out_signature="")
    def DisplayActionInformation(self, text, icon):
        # print(f"DisplayActionInformation: text: {text}, icon: {icon}")
        self.window.show_action_info_page(text)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="sy", out_signature="")
    def DisplayAction(self, text, icon):
        # print(f"DisplayAction: text: {text}, icon: {icon}")
        self.window.show_action_page(text)

    @dbus.service.method("org.ofono.SimToolkitAgent",
                    in_signature="sy", out_signature="b")
    def ConfirmOpenChannel(self, info, icon):
        # print(f"ConfirmOpenChannel: info: {info}, icon: {icon}")
        return self.window.show_confirm_open_channel_page(info)
