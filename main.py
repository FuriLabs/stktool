#!/usr/bin/env python3

import gi
from gi.repository import GLib, Gio

from sys import exit
from stktool.stk import StkApp

from asyncio import run, sleep

# these come from branchy. thank you jesus i love you
async def pump_gtk_events():
    main_context = GLib.MainContext.default()
    app = StkApp()
    app.connect('shutdown', lambda _: exit(0))

    Gio.Application.set_default(app)
    app.register()

    app.activate()

    while True:
        while main_context.pending():
            main_context.iteration(False)
        await sleep(1 / 160)

if __name__ == '__main__':
    run(pump_gtk_events())
