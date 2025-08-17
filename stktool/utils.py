# SPDX-License-Identifier: GPL-2.0
# Copyright (C) 2025 Bardia Moshiri <bardia@furilabs.com>

import dbus

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
