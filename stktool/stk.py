import gi
gi.require_version('Adw', '1')
from gi.repository import Adw

from stktool.stk_window import StkWindow

class StkApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='io.FuriOS.StkTool')
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = StkWindow(application=app)
        self.win.present()
