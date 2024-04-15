# TkEasyGUI

`TkEasyGUI` is a Python library that allows for the easy and simple creation of GUI applications.
In the event model, it is compatible with the well-known GUI library `PySimpleGUI`.

Python's standard UI library `Tkinter`, is often considered to have a high barrier to entry and to be difficult to use. By using this library, you can create GUI applications easily and intuitively.

This project adopts the lenient MIT license. This license will not change in the future. Let's enjoy creating GUI programs.

- [👉日本語](https://github.com/kujirahand/tkeasygui-python/blob/main/README-ja.md) / [👉中文](https://github.com/kujirahand/tkeasygui-python/blob/main/README-zh.md)

## Platform

- Windows / macOS / Linux (Tkinter required)

## Install

Install from pypi


```sh
python -m pip install TkEasyGUI
```

Install from GitHub Repository


```sh
python -m pip install git+https://github.com/kujirahand/tkeasygui-python
```

- (memo) Updating from older versions (less than 0.2.24) will fail. ([See the solution](https://github.com/kujirahand/tkeasygui-python/blob/main/docs/installation_trouble.md))

## How to use

To create a simple window with only labels and buttons, you would write as follows:

```py
import TkEasyGUI as eg
# define layout
layout = [[eg.Text("Hello, World!")],
          [eg.Button("Exit")]]
# create a window
with eg.Window("test", layout) as window:
    # event loop
    for event, values in window.event_iter():
        if event == "Exit":
            eg.popup("Thank you.")
            break
```

You can describe it using an event model similar to the famous GUI library, PySimpleGUI.

```py
import TkEasyGUI as eg
# define layout
layout = [[eg.Text("Hello, World!")],
          [eg.Button("Exit")]]
# create a window
window = eg.Window("test", layout)
# event loop
while True:
    event, values = window.read()
    if event in ["Exit", eg.WINDOW_CLOSED]:
        eg.popup("Thank you.")
        break
# close window
window.close()
```


## Samples

We have prepared a selection of samples to demonstrate simple usage. Please check them out.

- [samples](https://github.com/kujirahand/tkeasygui-python/tree/main/tests).

## Documents

Below is a detailed list of classes and methods.

- [docs](https://github.com/kujirahand/tkeasygui-python/tree/main/docs)

## About the relationship with PySimpleGUI

- When utilizing basic features, it is compatible with PySimpleGUI. You can write programs using the same event model as PySimpleGUI.
- The names of basic GUI components are also kept the same. However, while some property names differ, many unique features have been implemented.
- This project was developed with PySimpleGUI in mind, but has been implemented entirely from scratch. There are no licensing issues.
- We are not considering full compatibility with PySimpleGUI.

## Link

- [pypi.org > TkEasyGUI](https://pypi.org/project/tkeasygui/)
- [GitHub > TkEasyGUI](https://github.com/kujirahand/tkeasygui-python/)

