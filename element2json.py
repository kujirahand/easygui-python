#!/usr/bin/env python
"""
make elements.json and elements_test.py
"""
import json
import os

SCRIPT_DIR = os.path.dirname(__file__)

TEST_FILENAME = os.path.join(SCRIPT_DIR, "elements_test.py")
FILE_ELEMENTS = os.path.join(SCRIPT_DIR, "docs", "scripts", "elements.json")

COLS_PER_ROW = 4

def read_file() -> str:
    # read elements.json
    with open(FILE_ELEMENTS, "r", encoding="utf-8") as fp:
        elements = json.load(fp)
    args = {}
    for e in elements:
        args[e] = []
        if e in ["Button", "Text", "Input", "Frame", "Checkbox", "Label", "InputText", "Multiline"]:
            args[e].append(f"'{e}'")
        if e in ["Column", "Frame"]:
            args[e].append("layout=[[eg.Button('OK')]]")
        if e in ["Menu"]:
            args[e].append("menu_definition=[['File', ['Open', 'Save', 'Exit']], ['Edit', ['Copy', 'Paste']]]")
        if e in ["Table"]:
            args[e].append("values=[[1,2,3],[4,5,6],[7,8,9]]")
            args[e].append("headings=['aaa', 'bbb', 'ccc']")
        if e in ["Image"]:
            args[e].append("filename='a.png'")
            args[e].append("size=(100,100)")
        if e in ["Canvas"]:
            args[e].append("size=(100,100)")
        if e in ["Graph"]:
            args[e].append("size=(100,100)")
        if e in ["Combo"]:
            args[e].append("values=['combo1', 'combo2', 'combo3']")
            args[e].append("default_value='combo1'")
        if e in ["Listbox", "ListBrowse"]:
            args[e].append("values=['item1', 'item2', 'item3']")
        if e in ["Tab"]:
            args[e].append("title='tab'")
            args[e].append("layout=[[eg.Button('OK')]]")
        if e in ["TabGroup"]:
            args[e].append("layout=[[ eg.Tab('tab1', layout=[[eg.Button('OK')]]) ]]")
    return elements, args

def make_code():
    elements, init_args = read_file()
    src = """
### auto generated by element2json.py ###
# Test all elements of tkeasygui
import TkEasyGUI as eg
layout = [
"""
    src += "    [\n"
    for i, e in enumerate(elements):
        args = init_args.get(e, {})
        args_s = ",".join(args)
        if ("Browse" in e) or ("FileSaveAs" == e):
            src += f"        eg.Frame('{e}', layout=[[eg.Input(''), eg.{e}({args_s})]]),\n"
        else:
            src += f"        eg.Frame('{e}', layout=[[eg.{e}({args_s})]]),\n"
        if i % COLS_PER_ROW == (COLS_PER_ROW-1):
            src += "    ],\n"
            src += "    [\n"
    src += "    ],\n"
    src += "]\n"
    src += """
window = eg.Window(f"all element v.{eg.__version__}", layout=layout, size=(800, 600), font=("Arial", 12), resizable=True, show_scrollbar=True)
for event, values in window.event_iter():
    if event == "OK":
        break
"""
    print(f"==={TEST_FILENAME}===")
    print(src)
    with open("elements_test.py", "w", encoding="utf-8") as f:
        f.write(src)
    os.system("python elements_test.py")
if __name__ == "__main__":
    make_code()
