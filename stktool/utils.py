# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

from gi.repository import Gtk
import dbus
import re
from typing import Dict, Any, Optional

from bs4 import BeautifulSoup

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

def extract_dbus_data(data):
    if isinstance(data, dbus.Array):
        extracted = []
        for item in data:
            extracted.append(extract_dbus_data(item))
        return extracted
    elif isinstance(data, dbus.Struct):
        extracted = []
        for item in data:
            extracted.append(extract_dbus_data(item))
        return tuple(extracted)
    elif isinstance(data, (dbus.String, dbus.Byte, dbus.Int16, dbus.Int32, dbus.Int64,
                           dbus.UInt16, dbus.UInt32, dbus.UInt64, dbus.Double, dbus.Boolean)):
        return data.variant_level and str(data) or type(data).__bases__[0](data)
    elif isinstance(data, dict):
        extracted = {}
        for key, value in data.items():
            extracted[extract_dbus_data(key)] = extract_dbus_data(value)
        return extracted
    else:
        return data

def format_items_list(items):
    if not items:
        return "[]"

    formatted_items = []
    for item in items:
        if isinstance(item, (tuple, list)) and len(item) >= 1:
            title = item[0]
            formatted_items.append(f"   '{title}'")
        else:
            formatted_items.append(f"    {item}")

    return "\n" + "\n".join(formatted_items) + "\n"

def print_method_call(method_name, **kwargs):
    print(f"\n{method_name}")
    for key, value in kwargs.items():
        if key == 'items':
            extracted_items = extract_dbus_data(value)
            print(f"  {key}: {format_items_list(extracted_items)}")
        else:
            extracted_value = extract_dbus_data(value)
            print(f"  {key}: {extracted_value}")

def print_property_changed(name, value):
    print(f"  name: {name}")
    extracted_value = extract_dbus_data(value)
    if name == "MainMenu" and isinstance(extracted_value, list):
        print(f"  value: {format_items_list(extracted_value)}")
    else:
        print(f"  value: {extracted_value}")

def parse_stk_text(html_text: str) -> Dict[str, Any]:
    if not html_text or not html_text.strip():
        return {'text': '', 'segments': []}

    # If no HTML tags, return as plain text
    if '<' not in html_text:
        return {'text': html_text, 'segments': []}

    try:
        soup = BeautifulSoup(html_text, 'html.parser')

        plain_text = soup.get_text()
        segment = _find_deepest_styled_element(soup)
        segments = [segment] if segment else []

        return {
            'text': plain_text,
            'segments': segments
        }
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        plain_text = re.sub(r'<[^>]+>', '', html_text)
        return {'text': plain_text, 'segments': []}

def _find_deepest_styled_element(soup):
    styled_elements = soup.select('[style], [align]')

    if not styled_elements:
        return None

    deepest_element = None
    max_depth = -1

    for element in styled_elements:
        depth = len(list(element.parents))
        attributes = _extract_element_styling(element)

        # Only consider elements with meaningful styling
        if attributes and depth > max_depth:
            max_depth = depth
            deepest_element = element

    if deepest_element:
        return {
            'text': deepest_element.get_text().strip(),
            'attributes': _extract_element_styling(deepest_element),
            'start': 0,
            'end': len(deepest_element.get_text().strip())
        }

    return None

def _extract_element_styling(element):
    attributes = {}

    # Extract CSS styles
    if element.get('style'):
        css_styles = _parse_css_string(element['style'])
        attributes.update(css_styles)

    # Extract align attribute
    if element.get('align'):
        attributes['text-align'] = element['align']

    return attributes

def _parse_css_string(css_string):
    styles = {}

    # Parse CSS declarations
    declarations = re.findall(r'([^:;]+):([^:;]+)(?:;|$)', css_string)

    for prop, value in declarations:
        prop_clean = prop.strip()
        value_clean = value.strip()
        if prop_clean and value_clean:
            styles[prop_clean] = value_clean

    return styles

def apply_stk_formatting(widget, text: str):
    parsed = parse_stk_text(text)

    if isinstance(widget, Gtk.Label):
        _apply_to_label(widget, parsed)
    elif hasattr(widget, 'set_title'):
        widget.set_title(parsed.get('text', text))
    elif hasattr(widget, 'set_text'):
        widget.set_text(parsed.get('text', text))

def _apply_to_label(label: Gtk.Label, parsed_data: Dict[str, Any]):
    text = parsed_data.get('text', '')
    segments = parsed_data.get('segments', [])

    if not segments:
        label.set_text(text)
        return

    try:
        # Use the styled segment for formatting
        segment = segments[0]
        markup = _create_pango_markup(text, segment['attributes'])
        label.set_markup(markup)
    except Exception as e:
        print(f"Error applying markup: {e}")
        label.set_text(text)

def _create_pango_markup(text: str, attributes: dict) -> str:
    span_attrs = []

    if 'color' in attributes:
        color = _normalize_color(attributes['color'])
        if color:
            span_attrs.append(f'foreground="{color}"')

    if 'background-color' in attributes:
        bg_color = _normalize_color(attributes['background-color'])
        if bg_color:
            span_attrs.append(f'background="{bg_color}"')

    if 'font-weight' in attributes:
        weight = attributes['font-weight'].lower()
        if weight in ['bold', 'bolder', '700', '800', '900']:
            span_attrs.append('weight="bold"')

    if 'font-style' in attributes:
        style = attributes['font-style'].lower()
        if style == 'italic':
            span_attrs.append('style="italic"')

    if 'text-decoration' in attributes:
        decoration = attributes['text-decoration'].lower()
        if 'underline' in decoration:
            span_attrs.append('underline="single"')

    if span_attrs:
        escaped_text = (text.replace('&', '&amp;')
                            .replace('<', '&lt;')
                            .replace('>', '&gt;')
                            .replace('"', '&quot;'))

        return f'<span {" ".join(span_attrs)}>{escaped_text}</span>'
    else:
        return text

def _normalize_color(color_value: str) -> Optional[str]:
    if not color_value:
        return None

    color_value = color_value.strip()

    if color_value.startswith('#'):
        # should be #RGB or #RRGGBB
        if len(color_value) == 4 or len(color_value) == 7:
            if re.match(r'^#[0-9a-fA-F]+$', color_value):
                return color_value.lower()

    # RGB function format
    rgb_match = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
    if rgb_match:
        r, g, b = map(int, rgb_match.groups())
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    # RGBA function format (ignore alpha)
    rgba_match = re.match(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)', color_value)
    if rgba_match:
        r, g, b = map(int, rgba_match.groups()[:3])
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    color_names = {
        'red': '#ff0000', 'green': '#008000', 'blue': '#0000ff',
        'yellow': '#ffff00', 'black': '#000000', 'white': '#ffffff',
        'gray': '#808080', 'grey': '#808080', 'orange': '#ffa500',
        'purple': '#800080', 'brown': '#a52a2a', 'pink': '#ffc0cb',
        'cyan': '#00ffff', 'magenta': '#ff00ff', 'lime': '#00ff00',
        'maroon': '#800000', 'navy': '#000080', 'olive': '#808000',
        'silver': '#c0c0c0', 'teal': '#008080'
    }

    named_color = color_names.get(color_value.lower())
    if named_color:
        return named_color

    # If we can't parse the color, return it as-is
    # Pango might understand it, or it will ignore it
    return color_value

def create_formatted_label(text: str, css_classes: list = None) -> Gtk.Label:
    label = Gtk.Label()

    if css_classes:
        for css_class in css_classes:
            label.add_css_class(css_class)

    parsed_text = parse_stk_text(text)
    _apply_to_label(label, parsed_text)

    return label
