# FuncKeyRemap
Remap your Mac's function row keys. No root, no SIP disable, no accessibility API, no background process intercepting keys.

![TUI demo](demo.svg)

Basic TUI, no config file editing or hex code reformatting required.

I use it to make keyboard brightness buttons, and to set some to regular function keys for single press Shortcuts.app triggers. Even has some extra keys so you can make your caps lock escape or make the touch id/power button actually do something useful.

# Run it
Needs python, should run with Xcode's Command Line tools installed with no extra dependencies.
```
curl -L https://github.com/Bootlessjam/funcremap/raw/refs/heads/main/funcremap.py | python
```

# How it works
Builds off [Amarsyla's key-remapping-generator](https://github.com/amarsyla/hidutil-key-remapping-generator). Reads your keyboard's function key arrangement with `ioreg`, and remaps the keys with `hidutil`. Saves your remap to a login item that runs `hidutil` for persistence.

# If you have tokens to burn
- Would be nice to have a shell script version that doesn't need python.
- Would other keys be useful?