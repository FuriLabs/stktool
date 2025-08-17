# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import gi
from typing import Callable
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango
import re

def create_main_window_layout() -> tuple[Adw.ToastOverlay, Adw.NavigationView]:
    """Create the main window layout structure."""
    toast_overlay = Adw.ToastOverlay()
    navigation_view = Adw.NavigationView()
    toast_overlay.set_child(navigation_view)
    return toast_overlay, navigation_view

def create_non_swipeable_page(title: str) -> Adw.NavigationPage:
    """Create a non-swipeable navigation page."""
    page = Adw.NavigationPage(title=title)
    page.set_can_pop(False)
    return page

def create_main_page_content() -> tuple[Gtk.Box, Adw.StatusPage, Gtk.ScrolledWindow, Gtk.Box, Gtk.ListBox, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create the main page content structure."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

    main_menu_title = Adw.StatusPage()
    main_box.append(main_menu_title)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_min_content_height(400)
    scrolled_window.set_vexpand(True)
    main_box.append(scrolled_window)

    list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    scrolled_window.set_child(list_box)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    listbox.add_css_class("boxed-list")
    list_box.append(listbox)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    button_box.set_margin_top(12)
    button_box.set_margin_bottom(24)
    button_box.set_halign(Gtk.Align.CENTER)
    main_box.append(button_box)

    ok_button = Gtk.Button(label="OK")
    cancel_button = Gtk.Button(label="Cancel")

    button_box.append(ok_button)
    button_box.append(cancel_button)

    return main_box, main_menu_title, scrolled_window, list_box, listbox, button_box, ok_button, cancel_button

def create_unavailable_status_page() -> Adw.StatusPage:
    """Create status page for when STK is unavailable."""
    status_page = Adw.StatusPage()
    status_page.set_icon_name("dialog-warning-symbolic")
    status_page.set_title("SIM Toolkit Unavailable")
    status_page.set_description("SIM Toolkit is not available right now")
    return status_page

def create_display_text_dialog(parent, title: str, response_callback: Callable) -> Adw.MessageDialog:
    """Create display text dialog."""
    dialog = Adw.MessageDialog.new(parent)
    dialog.set_heading(title)

    dialog.add_response("no", "No")
    dialog.add_response("yes", "Yes")
    dialog.set_default_response("no")
    dialog.set_close_response("no")

    dialog.connect("response", response_callback)
    return dialog

def create_input_page_content(title: str, default: str, digits_only: bool = False) -> tuple[Gtk.Box, Gtk.Label, Adw.Clamp, Adw.EntryRow, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create input page content structure."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

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

    return box, title_label, clamp, entry, button_box, ok_button, cancel_button

def create_selection_page_content(title: str, items: list) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.ScrolledWindow, Gtk.ListBox, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create selection page content structure."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

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

    # Populate listbox with items
    for i, item in enumerate(items):
        title_text = re.sub(r'[^A-Za-z0-9 ]+', '', item[0]).strip()
        row = Adw.ActionRow(title=title_text)
        listbox.append(row)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    button_box.set_halign(Gtk.Align.CENTER)
    button_box.set_margin_top(12)
    button_box.set_margin_bottom(24)
    box.append(button_box)

    ok_button = Gtk.Button(label="OK")
    cancel_button = Gtk.Button(label="Cancel")
    button_box.append(ok_button)
    button_box.append(cancel_button)

    return box, status_page, scrolled_window, listbox, button_box, ok_button, cancel_button

def create_key_page_content(title: str, digits_only: bool = False) -> tuple[Gtk.Box, Gtk.Label, Adw.Clamp, Adw.EntryRow, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create key input page content structure."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

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

    return box, title_label, clamp, entry, button_box, ok_button, back_button

def create_confirmation_dialog(parent, title: str, info: str = None, url: str = None, response_callback: Callable = None) -> Adw.MessageDialog:
    """Create confirmation dialog."""
    dialog = Adw.MessageDialog.new(parent)
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

    dialog.add_response("no", "No")
    dialog.add_response("yes", "Yes")
    dialog.set_default_response("no")
    dialog.set_close_response("no")

    if response_callback:
        dialog.connect("response", response_callback)

    return dialog

def create_tone_dialog(parent, text: str, tone: str = None, response_callback: Callable = None) -> Adw.MessageDialog:
    """Create tone dialog."""
    dialog = Adw.MessageDialog.new(parent)
    dialog.set_heading(text)

    if tone:
        dialog.set_body(tone)

    dialog.add_response("end", "End Tone")
    dialog.set_default_response("end")
    dialog.set_close_response("end")

    if response_callback:
        dialog.connect("response", response_callback)

    return dialog

def create_loop_tone_dialog(parent, text: str, tone: str = None, response_callback: Callable = None) -> Adw.MessageDialog:
    """Create loop tone dialog."""
    dialog = Adw.MessageDialog.new(parent)
    dialog.set_heading(text)

    if tone:
        dialog.set_body(tone)

    dialog.add_response("wait", "Wait")
    dialog.add_response("end", "End Tone")
    dialog.set_default_response("end")
    dialog.set_close_response("end")

    if response_callback:
        dialog.connect("response", response_callback)

    return dialog

def create_action_info_dialog(parent, text: str) -> Adw.MessageDialog:
    """Create action info dialog."""
    dialog = Adw.MessageDialog.new(parent)
    dialog.set_heading(text)

    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")

    return dialog

def create_action_page_content(text: str) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.Box, Gtk.Button]:
    """Create action page content structure."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

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

    return box, status_page, button_box, ok_button

def create_confirm_open_channel_page_content(info: str) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create confirm open channel page content structure."""
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

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

    return box, status_page, button_box, yes_button, no_button

def create_toast(toast_overlay: Adw.ToastOverlay, message: str, duration: int = 3):
    """Create and show a toast message."""
    toast = Adw.Toast(title=message)
    toast_overlay.add_toast(toast)
    return toast

def setup_main_listbox_item(item_text: str) -> Adw.ActionRow:
    """Create a main menu listbox item."""
    row = Adw.ActionRow(title=item_text)
    return row
