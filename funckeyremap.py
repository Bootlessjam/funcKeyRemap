#!/usr/bin/env python

import curses
from curses import panel
import subprocess
import os
import xml.etree.ElementTree as ET

keycodes_mac_keys = [
    ("0x000C00000070", "display_brightness_down"),
    ("0x000C0000006F", "display_brightness_up"),
    ("0x000C000002A2", "launchpad"),
    ("0xFF0100000010", "mission_control"),
    ("0x000C00000221", "spotlight"),
    ("0x000C000000CF", "dictation"),
    ("0x00010000009B", "do_not_disturb"),
    ("0x00FF00000009", "keyboard_brightness_down"),
    ("0x00FF00000008", "keyboard_brightness_up"),
    ("0x000C000000B4", "rewind"),
    ("0x000C000000CD", "play_or_pause"),
    ("0x000C000000B3", "fast_forward"),
    ("0x000C000000EA", "volume_down"),
    ("0x000C000000E9", "volume_up"),
    ("0x000C000000E2", "mute"),
    ("0xFF0100000002", "dashboard")
]
keycodes_mac_keys_dups = [
    ("0xFF0100000021", 'display_brightness_down'),
    ("0x00FF00000005", "display_brightness_down"),
    ("0xFF0100000020", "display_brightness_up"),
    ("0x00FF00000004", "display_brightness_up"),
    ("0xFF0100000004", "launchpad"),
    ("0xFF0100000001", "spotlight")
]
keycodes_func_keys = [
    ("0x00070000003A", "F1"),
    ("0x00070000003B", "F2"),
    ("0x00070000003C", "F3"),
    ("0x00070000003D", "F4"),
    ("0x00070000003E", "F5"),
    ("0x00070000003F", "F6"),
    ("0x000700000040", "F7"),
    ("0x000700000041", "F8"),
    ("0x000700000042", "F9"),
    ("0x000700000043", "F10"),
    ("0x000700000044", "F11"),
    ("0x000700000045", "F12"),
    ("0x000700000068", "F13"),
    ("0x000700000069", "F14"),
    ("0x00070000006A", "F15"),
    ("0x00070000006B", "F16"),
    ("0x00070000006C", "F17"),
    ("0x00070000006D", "F18"),
    ("0x00070000006E", "F19")
]
extra_keys = [
    ("0x000700000029", "esc"),
    ("0x000700000039", "caps_lock"),
    ("0x000C00000040", "touch_id")
]
keytype_items = [
    ("macf", "Mac Function Key"),
    ("func", "Normal F key"),
    ("extra", "Extras"),
    ("default", "Default"),
    ("back","Back")
]


class Menu(object):
    """Interactive menu with curses, credit to https://stackoverflow.com/a/14205494"""

    def __init__(self, items, stdscreen, title):
        self.window = stdscreen.subwin(0, 0)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.position = 0
        self.items = items
        self.title = title

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = 0
        elif self.position >= len(self.items):
            self.position = len(self.items) - 1

    def display(self):
        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:
            self.window.refresh()
            self.window.addstr(0, 0, self.title)
            curses.doupdate()
            for index, item in enumerate(self.items):
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL
                msg = f"- {item[1]}"
                self.window.addstr(1 + index, 1, msg, mode)

            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord("\n")]:
                break

            elif key == curses.KEY_UP:
                self.navigate(-1)

            elif key == curses.KEY_DOWN:
                self.navigate(1)

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()
        return self.items[self.position][0]


class FuncRemap(object):
    """Main app class."""

    def get_keycode_name(self, hexkeycode):
        """Look through all of the stored keys to get the friendly name."""
        for code in keycodes_mac_keys+keycodes_func_keys+extra_keys+keycodes_mac_keys_dups:
            if code[0] == hexkeycode:
                return code[1]
        return "unknown"

    def save_config(self, remapped_keys):
        """Set the new mappings with hidutil command, and also saves the config to a login item."""
        # Create config string
        usermappings_string = "{\"UserKeyMapping\":["
        for src, dst in remapped_keys.items():
            usermappings_string += f"\n            {{\n              \"HIDKeyboardModifierMappingSrc\": {src},\n              \"HIDKeyboardModifierMappingDst\": {dst}\n            }},"
        # Remove last comma
        usermappings_string = usermappings_string[:-1]
        usermappings_string += "\n        ]}"

        # Write login script file
        plist_string = '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0">\n<dict>\n    <key>Label</key>\n    <string>com.local.KeyRemapping</string>\n    <key>ProgramArguments</key>\n    <array>\n        <string>/usr/bin/hidutil</string>\n        <string>property</string>\n        <string>--set</string>\n        <string>'
        plist_string += usermappings_string
        plist_string += '</string>\n    </array>\n    <key>RunAtLoad</key>\n    <true/>\n</dict>\n</plist>\n'
        with open(os.path.expanduser('~/Library/LaunchAgents/com.local.KeyRemapping.plist'), "w") as config_file:
            config_file.write(plist_string)

        # Set to current login too
        subprocess.run(f"hidutil property --set '{usermappings_string}'", shell=True)

    def main_loop(self):
        """Loop over the remapping flow, until exit is selected."""
        while True:
            # Read the login item to learn the current remaps
            current_remapped_keys = {}
            if os.path.isfile(os.path.expanduser('~/Library/LaunchAgents/com.local.KeyRemapping.plist')):
                configtree = ET.parse(os.path.expanduser('~/Library/LaunchAgents/com.local.KeyRemapping.plist'))
                configtext = configtree.getroot()[0][3][3].text
                for idx, line in enumerate(configtext.split('\n')):
                    if 'HIDKeyboardModifierMappingSrc' in line:
                        src = line.split(':')[1][1:-1]
                        dst = configtext.split('\n')[idx+1].split(':')[1][1:]
                        current_remapped_keys[src] = dst

            # Create main menu
            mainmenu_items = []
            for idx, key in enumerate(self.defaultfkeys):
                if key in list(current_remapped_keys):
                    mainmenu_items.append((key, (f"F{idx+1}: {self.get_keycode_name(current_remapped_keys[key])} (Changed)")))
                else:
                    mainmenu_items.append((key, (f"F{idx+1}: {self.get_keycode_name(key)} (Default)")))
            # Also add extra keys
            for key in extra_keys:
                if key[0] in list(current_remapped_keys):
                    mainmenu_items.append((key[0], f"{key[1]}: {self.get_keycode_name(current_remapped_keys[key[0]])} (Changed)"))
                else:
                    mainmenu_items.append((key[0], f"{key[1]} (Default)"))
            mainmenu_items.append(("exit", "Exit"))
            main_manu = Menu(mainmenu_items, self.screen, "Select Key to remap")
            key_to_remap = main_manu.display()
            if key_to_remap == "exit":
                break
            keytype_menu = Menu(keytype_items, self.screen, "Remap to?")
            keytype_selection = keytype_menu.display()
            keychoice_items = []
            if keytype_selection == "macf":
                keychoice_items = keycodes_mac_keys
            elif keytype_selection == "func":
                keychoice_items = keycodes_func_keys
            elif keytype_selection == "extra":
                keychoice_items = extra_keys
            elif keytype_selection == "back":
                continue
            elif keytype_selection == "default":
                if key_to_remap in list(current_remapped_keys):
                    del current_remapped_keys[key_to_remap]
                    self.save_config(current_remapped_keys)
                continue
            keychoice_items.append(("back", "Back"))
            key_choice_menu = Menu(keychoice_items, self.screen, "Key to remap to:")
            new_key_choice = key_choice_menu.display()
            if new_key_choice == "back":
                continue

            # Save and apply config
            current_remapped_keys[key_to_remap] = new_key_choice
            self.save_config(current_remapped_keys)

    def __init__(self, stdscreen):
        """Set up of curses and grabs the hardware function keycodes since they won't ever change."""
        self.screen = stdscreen
        curses.curs_set(0)
        # Get hardware keys from ioreg command
        self.defaultfkeys = []
        ioreg_output = subprocess.check_output(['ioreg', '-l'], text=True)
        for line in ioreg_output.split('\n'):
            if 'FnFunctionUsageMap' in line:
                # Decode the nonsense line
                for keyhex in line.split('"')[3].split(',')[1::2]:
                    # Turn it into a 32 bit uppercase hex, but save as a string...
                    self.defaultfkeys.append("0x"+(keyhex[2:6]+"0000"+keyhex[-4:]).upper())
        self.main_loop()


if __name__ == "__main__":
    f=open("/dev/tty")
    os.dup2(f.fileno(), 0)
    curses.wrapper(FuncRemap)
