# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import re
from typing import Callable

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw

from stktool.utils import parse_stk_text, apply_stk_formatting, create_formatted_label

def create_main_window_layout() -> tuple[Adw.ToastOverlay, Adw.NavigationView]:
    """Create the main window layout structure."""
    toast_overlay = Adw.ToastOverlay()
    navigation_view = Adw.NavigationView()
    toast_overlay.set_child(navigation_view)
    return toast_overlay, navigation_view

def create_non_swipeable_page(title: str) -> Adw.NavigationPage:
    """Create a non-swipeable navigation page."""
    # Parse title for formatting
    parsed_title = parse_stk_text(title)
    plain_title = parsed_title.get('text', title)

    page = Adw.NavigationPage(title=plain_title)
    page.set_can_pop(False)
    return page

def create_main_page_content() -> tuple[Gtk.Box, Adw.StatusPage, Gtk.ScrolledWindow, Gtk.Box, Gtk.ListBox, Gtk.Box, Gtk.Button, Gtk.Button, Adw.Banner]:
    """Create the main page content structure."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    # Status banner
    status_banner = Adw.Banner()
    status_banner.set_revealed(False)
    main_box.append(status_banner)

    # Main content
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_top(12)
    content_box.set_margin_bottom(12)
    content_box.set_margin_start(12)
    content_box.set_margin_end(12)
    main_box.append(content_box)

    main_menu_title = Adw.StatusPage()
    content_box.append(main_menu_title)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_min_content_height(300)
    scrolled_window.set_vexpand(True)
    content_box.append(scrolled_window)

    list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    scrolled_window.set_child(list_box)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    listbox.add_css_class("boxed-list")
    list_box.append(listbox)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    button_box.set_margin_top(12)
    button_box.set_margin_bottom(12)
    button_box.set_halign(Gtk.Align.CENTER)
    content_box.append(button_box)

    ok_button = Gtk.Button(label="Select")
    ok_button.add_css_class("suggested-action")
    ok_button.add_css_class("pill")

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.add_css_class("pill")

    button_box.append(ok_button)
    button_box.append(cancel_button)

    return main_box, main_menu_title, scrolled_window, list_box, listbox, button_box, ok_button, cancel_button, status_banner

def create_unavailable_status_page() -> Adw.StatusPage:
    """Create status page for when STK is unavailable."""
    status_page = Adw.StatusPage()
    status_page.set_title("SIM Toolkit Unavailable")
    status_page.set_description("No SIM card detected or SIM Toolkit services are not available")
    status_page.add_css_class("compact")
    return status_page

def create_loading_status_page() -> Adw.StatusPage:
    """Create loading status page."""
    status_page = Adw.StatusPage()
    status_page.set_title("Loading...")
    status_page.set_description("Connecting to SIM Toolkit services")

    # Add spinner
    spinner = Gtk.Spinner()
    spinner.set_spinning(True)
    spinner.set_size_request(32, 32)
    status_page.set_child(spinner)

    return status_page

def create_input_page_content(title: str, default: str, digits_only: bool = False) -> tuple[Gtk.Box, Adw.StatusPage, Adw.EntryRow, Gtk.Box, Gtk.Button, Gtk.Button, Gtk.Label]:
    """Create input page content structure."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    parsed_title = parse_stk_text(title)

    # Header with icon and title
    if parsed_title.get('segments'):
        header = Adw.StatusPage()
        header.add_css_class("compact")

        title_label = create_formatted_label(title, ["title-1"])
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_valign(Gtk.Align.CENTER)

        header.set_child(title_label)
    else:
        header = Adw.StatusPage()
        header.set_title(parsed_title.get('text', title))
        header.add_css_class("compact")

    main_box.append(header)

    # Content area
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_top(12)
    content_box.set_margin_bottom(12)
    content_box.set_margin_start(12)
    content_box.set_margin_end(12)
    main_box.append(content_box)

    entry = Adw.EntryRow(title="Input")
    entry.set_text(default)

    if digits_only:
        entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        entry.set_input_hints(Gtk.InputHints.NO_SPELLCHECK)

    content_box.append(entry)

    validation_label = Gtk.Label()
    validation_label.set_visible(False)
    validation_label.add_css_class("error")
    validation_label.set_halign(Gtk.Align.START)
    content_box.append(validation_label)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    button_box.set_halign(Gtk.Align.END)
    button_box.set_margin_top(12)
    content_box.append(button_box)

    ok_button = Gtk.Button(label="Confirm")
    ok_button.add_css_class("suggested-action")
    ok_button.add_css_class("pill")

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.add_css_class("pill")

    button_box.append(cancel_button)
    button_box.append(ok_button)

    def on_text_changed(entry_widget):
        text = entry_widget.get_text()
        is_valid = True
        error_message = ""

        # Digits-only validation
        if digits_only and text and not text.isdigit():
            is_valid = False
            error_message = "Only digits are allowed"

        if is_valid:
            entry_widget.remove_css_class("error")
            validation_label.set_visible(False)
            ok_button.set_sensitive(True)
        else:
            entry_widget.add_css_class("error")
            validation_label.set_text(error_message)
            validation_label.set_visible(True)
            ok_button.set_sensitive(False)

    entry.connect("notify::text", lambda *args: on_text_changed(entry))

    on_text_changed(entry)

    return main_box, header, entry, button_box, ok_button, cancel_button, validation_label

def create_selection_page_content(title: str, items: list) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.ScrolledWindow, Gtk.ListBox, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create selection page content structure."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    parsed_title = parse_stk_text(title)

    if parsed_title.get('segments'):
        header = Adw.StatusPage()
        header.add_css_class("compact")

        title_label = create_formatted_label(title, ["title-1"])
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_valign(Gtk.Align.CENTER)

        header.set_child(title_label)
    else:
        header = Adw.StatusPage()
        header.set_title(parsed_title.get('text', title))
        header.add_css_class("compact")

    main_box.append(header)

    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_top(12)
    content_box.set_margin_bottom(12)
    content_box.set_margin_start(12)
    content_box.set_margin_end(12)
    main_box.append(content_box)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_min_content_height(200)
    scrolled_window.set_max_content_height(400)
    scrolled_window.set_vexpand(True)
    content_box.append(scrolled_window)

    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
    listbox.add_css_class("boxed-list")
    scrolled_window.set_child(listbox)

    # Populate listbox with items
    for item in items:
        item_text = item[0] if isinstance(item, (tuple, list)) else str(item)
        parsed_item = parse_stk_text(item_text)

        if parsed_item.get('segments'):
            row = Gtk.ListBoxRow()
            row.set_activatable(True)

            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            item_box.set_margin_top(12)
            item_box.set_margin_bottom(12)
            item_box.set_margin_start(12)
            item_box.set_margin_end(12)

            item_label = create_formatted_label(item_text)
            item_label.set_halign(Gtk.Align.START)
            item_label.set_valign(Gtk.Align.CENTER)
            item_box.append(item_label)

            row.set_child(item_box)
        else:
            clean_text = re.sub(r'[^A-Za-z0-9 ]+', '', parsed_item.get('text', item_text)).strip()
            row = Adw.ActionRow(title=clean_text)

        listbox.append(row)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    button_box.set_halign(Gtk.Align.CENTER)
    button_box.set_margin_top(12)
    content_box.append(button_box)

    ok_button = Gtk.Button(label="Select")
    ok_button.add_css_class("suggested-action")
    ok_button.add_css_class("pill")

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.add_css_class("destructive-action")
    cancel_button.add_css_class("pill")

    button_box.append(cancel_button)
    button_box.append(ok_button)

    return main_box, header, scrolled_window, listbox, button_box, ok_button, cancel_button

def create_key_page_content(title: str, digits_only: bool = False) -> tuple[Gtk.Box, Adw.StatusPage, Adw.Clamp, Adw.EntryRow, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create key input page content structure with text attribute support."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

    parsed_title = parse_stk_text(title)

    # Header
    if parsed_title.get('segments'):
        header = Adw.StatusPage()
        header.set_description("Press any key" if not digits_only else "Press any digit")
        header.add_css_class("compact")

        title_label = create_formatted_label(title, ["title-1"])
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.set_valign(Gtk.Align.CENTER)

        header.set_child(title_label)
    else:
        header = Adw.StatusPage()
        header.set_title(parsed_title.get('text', title))
        header.set_description("Press any key" if not digits_only else "Press any digit")
        header.add_css_class("compact")

    main_box.append(header)

    # Content area
    content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    content_box.set_margin_top(12)
    content_box.set_margin_bottom(12)
    content_box.set_margin_start(12)
    content_box.set_margin_end(12)
    main_box.append(content_box)

    clamp = Adw.Clamp()
    content_box.append(clamp)

    entry = Adw.EntryRow(title="Key")
    entry.set_text("")
    if digits_only:
        entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        entry.set_input_hints(Gtk.InputHints.NO_SPELLCHECK)

    clamp.set_child(entry)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    button_box.set_halign(Gtk.Align.End)
    button_box.set_margin_top(12)
    content_box.append(button_box)

    back_button = Gtk.Button(label="Back")
    back_button.add_css_class("pill")

    ok_button = Gtk.Button(label="Confirm")
    ok_button.add_css_class("suggested-action")
    ok_button.add_css_class("pill")

    button_box.append(back_button)
    button_box.append(ok_button)

    return main_box, header, clamp, entry, button_box, ok_button, back_button

def create_window_controls(window):
    """Set up window behavior."""
    window.set_title("SIM Toolkit")

def create_toast(toast_overlay: Adw.ToastOverlay, message: str, duration: int = 3):
    print(message)
    """Create toast message."""
    parsed_msg = parse_stk_text(message)
    plain_message = parsed_msg.get('text', message)

    toast = Adw.Toast(title=plain_message)
    toast.set_timeout(duration)
    toast_overlay.add_toast(toast)
    return toast

def create_confirmation_dialog(title: str, info: str = None, url: str = None, response_callback: Callable = None) -> Adw.AlertDialog:
    """Create confirmation dialog."""
    dialog = Adw.AlertDialog()

    parsed_title = parse_stk_text(title)
    dialog.set_heading(parsed_title.get('text', title))

    body_text = ""
    if info:
        parsed_info = parse_stk_text(info)
        body_text += parsed_info.get('text', info)
    if url:
        if body_text:
            body_text += "\n\n"
        body_text += f"URL: {url}"

    if body_text:
        dialog.set_body(body_text)

    dialog.add_response("cancel", "Cancel")
    dialog.add_response("confirm", "Confirm")
    dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    if response_callback:
        def handle_response(dialog, response):
            response_callback(dialog, "yes" if response == "confirm" else "no")
        dialog.connect("response", handle_response)

    return dialog

def create_tone_dialog(text: str, tone: str = None, response_callback: Callable = None) -> Adw.AlertDialog:
    """Create tone dialog with text attribute support."""
    dialog = Adw.AlertDialog()

    parsed_text = parse_stk_text(text)
    dialog.set_heading(parsed_text.get('text', text))

    if tone:
        dialog.set_body(f"Tone: {tone}")

    dialog.add_response("end", "End Tone")
    dialog.set_default_response("end")
    dialog.set_close_response("end")

    if response_callback:
        dialog.connect("response", response_callback)

    return dialog

def create_loop_tone_dialog(text: str, tone: str = None, response_callback: Callable = None) -> Adw.AlertDialog:
    """Create loop tone dialog."""
    dialog = Adw.AlertDialog()

    parsed_text = parse_stk_text(text)
    dialog.set_heading(parsed_text.get('text', text))

    if tone:
        dialog.set_body(f"Tone: {tone}")

    dialog.add_response("wait", "Wait")
    dialog.add_response("end", "End Tone")
    dialog.set_response_appearance("wait", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("end")
    dialog.set_close_response("end")

    if response_callback:
        dialog.connect("response", response_callback)

    return dialog

def create_action_info_dialog(text: str) -> Adw.AlertDialog:
    """Create action info dialog."""
    dialog = Adw.AlertDialog()
    dialog.set_heading("Action Information")

    parsed_text = parse_stk_text(text)
    dialog.set_body(parsed_text.get('text', text))

    dialog.add_response("ok", "OK")
    dialog.set_default_response("ok")
    dialog.set_close_response("ok")

    return dialog

def create_action_page_content(text: str) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.Box, Gtk.Button]:
    """Create action page content structure."""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_top(12)
    main_box.set_margin_bottom(12)
    main_box.set_margin_start(12)
    main_box.set_margin_end(12)

    status_page = Adw.StatusPage()
    status_page.set_title("Action")

    parsed_text = parse_stk_text(text)
    status_page.set_description(parsed_text.get('text', text))
    main_box.append(status_page)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    button_box.set_halign(Gtk.Align.CENTER)
    main_box.append(button_box)

    ok_button = Gtk.Button(label="Continue")
    ok_button.add_css_class("suggested-action")
    ok_button.add_css_class("pill")
    button_box.append(ok_button)

    return main_box, status_page, button_box, ok_button

def create_confirm_open_channel_page_content(info: str) -> tuple[Gtk.Box, Adw.StatusPage, Gtk.Box, Gtk.Button, Gtk.Button]:
    """Create confirm open channel page content structure"""
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    main_box.set_margin_top(12)
    main_box.set_margin_bottom(12)
    main_box.set_margin_start(12)
    main_box.set_margin_end(12)

    status_page = Adw.StatusPage()
    status_page.set_title("Confirm Open Channel")

    parsed_info = parse_stk_text(info)
    status_page.set_description(parsed_info.get('text', info))
    main_box.append(status_page)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    button_box.set_halign(Gtk.Align.CENTER)
    main_box.append(button_box)

    no_button = Gtk.Button(label="Deny")
    no_button.add_css_class("destructive-action")
    no_button.add_css_class("pill")

    yes_button = Gtk.Button(label="Allow")
    yes_button.add_css_class("suggested-action")
    yes_button.add_css_class("pill")

    button_box.append(no_button)
    button_box.append(yes_button)

    return main_box, status_page, button_box, yes_button, no_button

def setup_main_listbox_item(item_text: str) -> Gtk.Widget:
    """Create main menu listbox item."""
    parsed_item = parse_stk_text(item_text)

    if parsed_item.get('segments'):
        row = Gtk.ListBoxRow()
        row.set_activatable(True)

        item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        item_box.set_margin_top(12)
        item_box.set_margin_bottom(12)
        item_box.set_margin_start(12)
        item_box.set_margin_end(12)

        item_label = create_formatted_label(item_text)
        item_label.set_halign(Gtk.Align.START)
        item_label.set_valign(Gtk.Align.CENTER)
        item_box.append(item_label)

        row.set_child(item_box)
        return row
    else:
        clean_text = parsed_item.get('text', item_text)
        row = Adw.ActionRow(title=clean_text)
        row.set_activatable(True)
        return row
