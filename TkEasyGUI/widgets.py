"""
TkEasyGUI Widgets
"""
import io
import os
import platform
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from queue import Queue
from tkinter import font as tkinter_font
from tkinter import scrolledtext, ttk
from typing import Any, Union

# from typing import TypeAlias
from PIL import Image as PILImage
from PIL import ImageTk

from . import dialogs, utils, version
from .utils import (
    # type alias
    Element,
    EventMode,
    FontType,
    ListboxSelectMode,
    OrientationType,
    PadType,
    PointType,
    ReliefType,
    TextAlign,
    TextVAlign,
    # Window,
    _window_count,
    _window_parent,
    _window_pop,
    _window_push,
    generate_element_id,
    generate_element_style_key,
    get_current_theme,
    get_root_window,
    get_ttk_style,
    register_element_key,
)

#------------------------------------------------------------------------------
# Const
#------------------------------------------------------------------------------
WINDOW_CLOSED: str = "WINDOW_CLOSED"
WIN_CLOSED: str = "WINDOW_CLOSED"
WINDOW_TIMEOUT: str = "-TIMEOUT-"
TIMEOUT_KEY: str = WINDOW_TIMEOUT
WINDOW_KEY_EVENT: str = "-WINDOW_KEY_EVENT-"
LISTBOX_SELECT_MODE_MULTIPLE: str = "multiple"
LISTBOX_SELECT_MODE_BROWSE: str = "browse"
LISTBOX_SELECT_MODE_EXTENDED: str = "extended"
LISTBOX_SELECT_MODE_SINGLE: str = "single"
TABLE_SELECT_MODE_NONE: str = tk.NONE
TABLE_SELECT_MODE_BROWSE: str = tk.BROWSE
TABLE_SELECT_MODE_EXTENDED: str = tk.EXTENDED
EG_SWAP_EVENT_NAME: str = "--swap_event_name--"

# about color (Thanks)
# https://kuroro.blog/python/YcZ6Yh4PswqUzaQXwnG2/


#------------------------------------------------------------------------------
# Widget wrapper
#------------------------------------------------------------------------------
class TkEasyError(Exception):
    def __init__(self, message="TkEasyError"):
        self.message = message
        super().__init__(self.message)

class Window:
    """
    Main window object in TkEasyGUI
    """
    def __init__(
        self,
        title: str,
        layout: list[list[Element]],  # set elements layout
        size: Union[tuple[str, int], None] = None,  # window size
        resizable: bool = False,
        font: Union[FontType, None] = None,
        modal: bool = False,  # modal window
        keep_on_top: bool = False,  # keep on top
        no_titlebar: bool = False,  # hide titlebar
        grab_anywhere: bool = False,  # can move window by dragging anywhere
        alpha_channel: float = 1.0,  # window alpha channel
        enable_key_events: bool = False,  # enable keyboard events
        return_keyboard_events: bool = False,  # enable keyboard events (for compatibility)
        location: Union[tuple[int, int], None] = None,  # window location
        center_window: bool = True,  # move window to center
        row_padding: int = 2,  # row padding
        padding_x: int = 8,  # x padding around the window
        padding_y: int = 8,  # y padding around the window
        icon: Union[str, None] = None,  # window icon, specify filename (Experimental)
        show_scrollbar: bool = False,  # show scrollbar (Experimental)
        **kw,
    ) -> None:
        """Create a window with a layout of widgets."""
        self.modal: bool = modal
        # check active window
        active_win = utils._get_active_window()
        if active_win is None:
            active_win = get_root_window()
        self.title: str = title
        self.window: tk.Toplevel = tk.Toplevel(master=active_win)
        self.timeout: Union[int, None] = None
        self.timeout_key: str = WINDOW_TIMEOUT
        self.timeout_id: Union[str, None] = None
        self.events: Queue = Queue()
        self.key_elements: dict[str, Element] = {}
        self.last_values: dict[str, Any] = {}
        self.flag_alive: bool = True # Pressing the close button will turn this flag to False.
        self.layout: list[list[Element]] = layout
        self._event_hooks: dict[str, list[callable]] = {}
        self.font: Union[FontType, None] = font
        self.radio_group_dict: dict[str, list[tk.IntVar, int]] = {}
        self.minimized: bool = False
        self.maximized: bool = False
        self.is_hidden: bool = False
        self._keep_on_top: bool = keep_on_top
        self._no_titlebar: bool = no_titlebar
        self._grab_anywhere: bool = grab_anywhere
        self._grab_flag: bool = False
        self._start_x: Union[int, None] = None
        self._start_y: Union[int, None] = None
        self._mouse_x: Union[int, None] = None
        self._mouse_y: Union[int, None] = None
        self.alpha_channel: float = alpha_channel
        self.enable_key_events: bool = enable_key_events
        self.return_keyboard_events: bool = return_keyboard_events
        self.font_size_average: tuple[int, int] = (12, 10)
        self.row_padding: int = row_padding
        self.center_window: bool = center_window
        self.padding_x: int = padding_x
        self.padding_y: int = padding_y
        self.show_scrollbar = show_scrollbar  # (experimental)
        self._icon: Union[Any, None] = None
        if icon is not None:
            self.set_icon(icon)
        # Canvas
        self.canvas: Union[tk.Canvas, None] = None
        if show_scrollbar:
            self.canvas = tk.Canvas(self.window)
            self.canvas.pack(
                side=tk.LEFT, fill=tk.BOTH, expand=True,
                padx=padding_x, pady=padding_y
            )
            # scrollbar
            self.frame_bar = tk.Scrollbar(
                self.window,
                orient=tk.VERTICAL, 
                command=self.canvas.yview
            )
            self.frame_bar.pack(side=tk.RIGHT, fill=tk.Y)
            self.canvas.configure(yscrollcommand=self.frame_bar.set)
            # Frame
            self.frame: tk.Frame = tk.Frame(self.canvas)
            self.canvas.create_window((0, 0), window=self.frame, anchor=tk.NW)
        else:
            self.frame: tk.Frame = tk.Frame(self.window)
            self.frame.pack(expand=True, fill="both", padx=padding_x, pady=padding_y)
        # self.frame.configure(style="TFrame")
        # set window properties
        self.set_title(title)
        self.window.protocol("WM_DELETE_WINDOW", lambda : self._close_handler())
        self.size: Union[tuple[int, int], None] = size
        if size is not None:
            self.set_size(size)
        self.window.resizable(resizable, resizable)
        # create widgets
        self._create_widget(self.frame, layout)
        # pack frame
        self.frame.rowconfigure(0, weight=1)
        if keep_on_top:
            self.window.attributes("-topmost", True)
        if no_titlebar:
            self.window.after_idle(self.hide_titlebar, True)
        if grab_anywhere:
            self.set_grab_anywhere(True)
        if alpha_channel < 1.0:
            self.set_alpha_channel(alpha_channel)
        # font
        self._calc_font_size(font)
        # bind events
        if self.enable_key_events:
            self.window.bind("<Key>", lambda e: self._event_handler(
                WINDOW_KEY_EVENT,
                {"event": e, "key": e.keysym, "event_type": "key"}))
        if self.return_keyboard_events: # for compatibility with PySimpleGUI
            self.window.bind("<Key>", lambda e: self._event_handler(
                e.keysym if len(e.keysym) == 1 else f"{e.keysym}:{e.keycode}", {}))
        # check modal
        if modal:
            # set modal action
            self.window.attributes("-topmost", 1) # topmost
            # self.window.transient(parent)
            self.window.grab_set()
            self.window.focus_force()
        # push window
        self.parent_window: Union[Window, None] = _window_parent()
        _window_push(self)
        # set show event
        self.window.bind("<Map>", self._on_window_show)
        # set window size
        self.frame.bind("<Configure>", self._on_frame_configure)
        # position
        if location is not None:
            self.set_location(location)
        else:
            # could not get size with geometry() before window is shown
            # so, move window to center after window is shown `_on_window_show`
            pass

    def _on_frame_configure(self, _event):
        """Handle frame configure event."""
        # set scrollbar
        if self.canvas is None:
            return
        region = self.canvas.bbox("all")
        self.canvas.configure(scrollregion=region)
        # set size
        pre_size = self.size
        w, h = region[2], region[3]
        sw, sh = self.get_screen_size()
        pad_x = self.padding_x * 2
        pad_y = self.padding_y * 2
        if (pre_size is None):
            if w > sw:
                w = sw - pad_x
            if h > sh:
                h = sh - pad_y
            self.set_size((w + pad_x, h + pad_y))
            self.size = pre_size

    def _on_window_show(self, *event) -> None:
        """Handle window show event."""
        if self.center_window:
            if self.parent_window is None: # only this window
                self.move_to_center()
            else:
                self.move_to_center(center_pos=self.parent_window.get_center_location())
        self.update_idle_tasks()

    def set_location(self, xy: tuple[int, int]) -> None:
        """Set window location."""
        self.window.geometry(f"+{xy[0]}+{xy[1]}")
    
    def get_location(self) -> tuple[int, int]:
        """Get window location."""
        loc = self.window.geometry().split("+")
        return (int(loc[1]), int(loc[2]))

    def get_center_location(self) -> tuple[int, int]:
        """Get center location."""
        w, h = self.get_size()
        x, y = self.get_location()
        return (x + w // 2, y + h // 2)

    def __enter__(self):
        """Initialize resource"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalize resource"""
        self.close()
    
    def register_event_hooks(self, hooks: dict[str, list[callable]]) -> None:
        """
        Register event hooks. (append hook events)

        **Example**
        ```py
        window.register_event_hooks({
            "-input-": [
                lambda event, values: print("1", event, values),
                lambda event, values: print("2", event, values),
                lambda event, values: True, # stop event propagation
                lambda event, values: print("3", event, values),
            ],
        ```

        **Note**
        - If you specify a function that returns True, it changes the event name to f"{event}-stopped" and then re-collects the values associated with keys that occur afterwards.
        - @see [Window.read](#windowread)
        """
        for event_name, handle_list in hooks.items():
            for handle in handle_list:
                if event_name not in self._event_hooks:
                    self._event_hooks[event_name] = []
                self._event_hooks[event_name].append(handle)
    
    def _create_widget(self, parent: tk.Widget, layout: list[list["Element"]], align: TextAlign="left", valign: TextVAlign="top"):
        """create widget from layout"""
        # check layout
        if not (len(layout) > 0 and (isinstance(layout[0], list) or isinstance(layout[0], tuple))):
            raise TkEasyError(f"Invalid layout, should specify a two-dimensional list: {layout}")
        # prepare create
        for widgets in layout:
            for elem in widgets:
                elem.prepare_create(self)
        # create widgets
        self.need_focus_widget: tk.Widget|None = None
        for row_no, widgets in enumerate(layout):
            bgcolor = None
            if parent is not None:
                try:
                    bgcolor = parent.cget("background")
                except Exception:
                    pass
            frame_prop = {"name": f"tkeasygui_frame_row_{row_no}"}
            if bgcolor is not None:
                frame_prop["background"] = bgcolor
            frame_row = tk.Frame(parent, **frame_prop)
            # columns
            prev_element: Element|None = None
            row_pack_prop: dict[str, Any] = {
                "expand": False,
                "fill": "x",
                "side": valign,
                "pady": self.row_padding,
            }
            # reversed?
            if align == "right":
                widgets = reversed(widgets)
            for col_no, elemment in enumerate(widgets):
                # create widget
                elem: Element = elemment
                # set window and parent
                elem.window = self
                elem.parent = frame_row
                elem.col_no = col_no
                elem.row_no = row_no
                # set prev_element and next_element
                elem.prev_element = prev_element # set prev_element
                if prev_element is not None:
                    prev_element.next_element = elem
                prev_element = elem
                # create widget
                try:
                    elem_parent = frame_row
                    if type(parent) == ttk.Notebook:
                        elem_parent = parent
                    widget: tk.Widget = elem.create(self, elem_parent)
                    widget.__tkeasygui = elem # type : ignore
                except Exception as e:
                    print(e.__traceback__, file=sys.stderr)
                    raise TkEasyError(
                        f"Window._create_widget.Failed `{elem.element_type}` key=`{elem.get_name()}` {elem.props} reason:{e}"
                    ) from e
                # check key
                if elem.has_value or (elem.key is not None):
                    self.key_elements[elem.key] = elem
                # check focus widget
                if elem.has_value and (self.need_focus_widget is None):
                    self.need_focus_widget = widget
                # check specila key
                if (self.need_focus_widget is None) and (elem.key == "OK" or elem.key == "Yes"):
                    self.need_focus_widget = widget
                # create sub widgets
                try:
                    # has children?
                    if elem.has_children:
                        self._create_widget(widget, elem.layout, align=elem.text_align, valign=elem.vertical_alignment)
                except Exception as e:
                    print(e.__traceback__, file=sys.stderr)
                    raise TkEasyError(
                        f"Window._create_widget.Failed(children) `{elem.element_type}` key=`{elem.key}` {elem.props} reason:{e}"
                    ) from e
                # post create
                elem.post_create(self, frame_row)
                # bind event (before create)
                for event_name, handle_t in elem._bind_dict.items():
                    self.bind(elem, event_name, handle_t[0], handle_t[1], handle_t[2])
                # menu ?
                if isinstance(elem, Menu):
                    continue
                # Tab?
                if isinstance(parent, ttk.Notebook):
                    # print("@@@@ TabGroup", type(parent), type(elem.widget), elem.get())
                    parent.add(elem.widget, text=elem.get())
                    if isinstance(elem, Tab):
                        group:TabGroup = parent.__tkeasygui
                        tab: Tab = elem
                        if group.max_rows > tab.rows:
                            tab.rows = group.max_rows
                        if group.max_cols > tab.cols:
                            tab.cols = group.max_cols
                    continue
                # pack widget
                fill_props = elem._get_pack_props(align, valign)
                widget.pack(**fill_props)
                # expand_y?
                if elem.expand_y:
                    row_pack_prop["expand"] = True
                    row_pack_prop["fill"] = "both"
                # pady
                if elem.pady is not None:
                    row_pack_prop["pady"] = elem.pady
            # add row
            frame_row.pack(**row_pack_prop)
        # end of create
        if self.need_focus_widget is not None:
            self.need_focus_widget.focus_set()

    def _calc_font_size(self, font: FontType) -> None:
        """Calculate font size."""
        font_obj = tkinter_font.Font()
        if font is not None:
            if len(font) >= 2:
                font_obj = tkinter_font.Font(family=font[0], size=font[1])
            elif len(font) == 1:
                font_obj = tkinter_font.Font(family=font[0])
        # calc measure
        # The letter 'M' is commonly used to represent the average width of a font in typography. This is because the 'M' is relatively wide, making it suitable for indicating width in comparison to other characters, especially in fixed-width (monospace) fonts.
        m_size = font_obj.measure("M")
        s_size = font_obj.measure("s")
        a_size = font_obj.measure("A")
        w = (m_size + s_size + a_size) // 3
        h = font_obj.metrics("linespace")
        self.font_size_average = (w, h)
    
    def move(self, x: int, y: int) -> None:
        """Move the window. (same as set_location)"""
        self.set_location((x, y))

    def get_screen_size(self) -> tuple[int, int]:
        """Get the screen size."""
        root = get_root_window()
        return (root.winfo_screenwidth(), root.winfo_screenheight())
    
    def update_idle_tasks(self) -> None:
        """Update idle tasks."""
        self.window.update_idletasks()
 
    def move_to_center(self, center_pos: Union[tuple[int, int], None] = None) -> None:
        """Move the window to the center of the screen."""
        if center_pos is None:
            w, h = self.get_screen_size()
            cx, cy = w // 2, h // 2
        else:
            cx, cy = center_pos
        try:
            if self.size is None:
                win_x, win_y = self.get_size()
                if win_x < 10 or win_y < 10:
                    win_x = 600 # TODO: 適当なサイズ
                    win_y = 400
            else:
                win_x, win_y = self.size
            x = (cx - win_x // 2)
            y = (cy - win_y // 2)
            # It will be out of range, so move it to the center.
            if x < 0 or y < 0:
                w, h = self.get_screen_size()
                cx, cy = w // 2, h // 2
                x = cx - win_x // 2
                y = cy - win_y // 2
            self.move(x, y)
        except Exception as _:
            pass
    def get_size(self) -> tuple[int, int]:
        """Get the window size."""
        size = self.window.geometry().split("+")[0].split("x")
        return (int(size[0]), int(size[1]))

    def get_element_by_key(self, key: str) -> Union[Element, None]:
        """Get an element by its key."""
        return self.key_elements[key] if key in self.key_elements else None
    
    def get_elements_by_type(self, element_type: str) -> list[Element]:
        """Get elements by type."""
        result: list[Element] = []
        for rows in self.layout:
            for elem in rows:
                if elem.element_type.lower() == element_type.lower():
                    result.append(elem)
        return result

    def read(self, timeout: Union[int, None] = None, timeout_key: str="-TIMEOUT-") -> tuple[str, dict[str, Any]]:
        """ Read events from the window."""
        self.timeout = timeout
        self.timeout_key = timeout_key
        timeout_chcker_id = time_checker_start()
        # get root window
        root = get_root_window()
        # update window before mainloop
        root.update() 
        # set focus timer (once when window show)
        self.window.after("idle", _focus_window, self)
        # mainloop for hook
        key, values = (None, {}) # set default key and values
        # mainloop - read a event
        while True:
            # set timeout
            if self.timeout_id is not None:
                self.window.after_cancel(self.timeout_id)
            self.window.update_idletasks()
            self.timeout_id = self.window.after("idle", self._window_idle_handler)
            # -----------------------------------------------------
            # mainloop - should be called only once
            # -----------------------------------------------------
            root.mainloop()
            # -----------------------------------------------------
            # after mainloop, check events
            # -----------------------------------------------------
            # timeout ?
            if timeout is not None:
                # check interval
                interval = time_checker_end(timeout_chcker_id)
                if interval > timeout:
                    key, values = (self.timeout_key, {}) # create timeout event
                    return (key, values)
            # get ui event
            if self.events.empty():
                continue
            key, values = self.events.get()
            # _event_hooks
            if key in self._event_hooks:
                flag_stop = self._dispatch_event_hooks(key, values)
                if flag_stop:
                    key = f"{key}-stopped" # change event name
                    values = self.get_values() # collect values again
            # If an event hidden from the user occurs, continue to use the mainloop.
            if isinstance(key, str) and key.endswith("/hide"):
                continue # hide system events
            # return a event
            break
        return (key, values)

    def event_iter(self, timeout: Union[int, None] = None, timeout_key: str=TIMEOUT_KEY) -> Any:
        """
        Return generator with event and values
        **Example**
        ```py
        import TkEasyGUI as eg
        # create a window
        with eg.Window("test", layout=[[eg.Button("Hello")]]) as window:
            # event loop
            for event, values in window.event_iter():
                if event == "Hello":
                    eg.popup("Hello, World!")
        ```
       """
        # event loop
        while self.is_alive():
            event, values = self.read(timeout=timeout, timeout_key=timeout_key)
            yield (event, values)

    def _dispatch_event_hooks(self, key: str, values: dict[str, Any]) -> bool:
        """Dispatch event hooks."""
        # execute _event_hooks
        flag_stop = False
        if key in self._event_hooks:
            for handle in self._event_hooks[key]:
                result = handle(key, values)
                if result is True:
                    flag_stop = True
                    break
        return flag_stop
    
    def set_size(self, size: tuple[int, int]) -> None:
        """Set the window size."""
        self.window.geometry(f"{size[0]}x{size[1]}")
        self.size = size
    
    def set_title(self, title: str) -> None:
        """Set the title of the window."""
        self.window.title(title)
        self.title = title

    def minimize(self) -> None:
        """Minimize the window."""
        self.window.iconify()
        self.minimized = True

    def normal(self) -> None:
        """set normal window."""
        if self.minimized:
            self.window.deiconify()
            self.minimized = False
        if self.maximized:
            self.window.state("normal")
            self.maximized = False

    def hide(self) -> None:
        """Hide the window."""
        self.window.withdraw()
        self.is_hidden = True

    def un_hide(self) -> None:
        """Un hide the window."""
        if self.is_hidden:
            self.window.deiconify()
            self.is_hidden = False

    def maximize(self) -> None:
        """Maximize the window. (`resizable` should be set to True)"""
        self.window.state("zoomed")
        self.maximized = True
    
    def set_alpha_channel(self, alpha: float) -> None:
        """Set the alpha channel of the window."""
        self.window.attributes("-alpha", alpha)
        self.alpha_channel = alpha

    def get_values(self) -> dict[str, Any]:
        """Get values from the window."""
        values: dict[str, Any] = {}
        for key,val in self.key_elements.items():
            if not val.has_value:
                continue
            # get value from widget if possible
            try:
                values[key] = val.get()
            except Exception:
                # if not possible, return last_values
                return self.last_values
        # set cache
        self.last_values = values
        return values

    def _window_idle_handler(self) -> None:
        """Handle window idle event."""
        _exit_mainloop()

    def _event_handler(self, key: str, values: Union[dict[str, Any], None]) -> None:
        """Handle an event."""
        # set value
        if values is None:
            values = {}
        for k, v in self.get_values().items():
            values[k] = v
        # check EG_SWAP_EVENT_NAME
        if EG_SWAP_EVENT_NAME in values:
            key = values.pop(EG_SWAP_EVENT_NAME)
        # put event
        self.events.put((key, values))
        _exit_mainloop()
    
    def _exit_main_loop(self) -> None:
        """Exit mainloop"""
        if self.timeout_id is not None:
            self.window.after_cancel(self.timeout_id)
        _exit_mainloop()

    def _close_handler(self):
        """Handle a window close event."""
        self.flag_alive = False
        if self.timeout_id is not None:
            self.window.after_cancel(self.timeout_id)
        self._event_handler(WINDOW_CLOSED, None)
    
    def keep_on_top(self, flag: bool) -> None:
        """Set the window to keep on top."""
        self.window.attributes("-topmost", flag)
        self._keep_on_top = flag
    
    def send_to_back(self) -> None:
        """Send the window to the back, and make it not keep on top."""
        self.window.attributes("-topmost", False)
        self._keep_on_top = False
        self.window.lower()

    def hide_titlebar(self, flag: bool) -> None:
        """Hide the titlebar."""
        try:
            self.window.overrideredirect(flag)
            self._no_titlebar = flag
        except Exception:
            pass

    def close(self) -> None:
        """Close the window."""
        # The phenomenon where a closed window remains visible is occurring, so forcibly making it transparent.
        try:
            self.set_alpha_channel(0.0) # force hide
        except Exception as _:
            pass
        try:
            self.hide()
        except Exception as _:
            pass
        # already closed?
        if not self.flag_alive:
            return
        # close window
        try:
            self.flag_alive = False
            _window_pop(self)
            self.window.destroy() # close window
            win_count = _window_count()
            if win_count == 0:
                self.window.quit() # quit app
        except Exception as e:
            print(f"Window.close.failed: {e}", file=sys.stderr)
            pass

    def is_alive(self) -> bool:
        """Check if the window is alive."""
        return self.flag_alive
    
    def is_running(self) -> bool:
        """Check if the window is running. (alias as is_alive)"""
        return self.flag_alive
    
    def cancel_close(self) -> None:
        """Cancel the close event."""
        self.flag_alive = True
    
    def write_event_value(self, key: str, values: dict[str, Any]) -> None:
        self.events.put((key, values))
    
    def __getitem__(self, key: str) -> Any:
        """Get an element by its key."""
        return self.key_elements[key]
    
    def show(self) -> None:
        """ Show hidden window (hide -> show)"""
        # check status
        if self.is_hidden:
            self.un_hide()
        if self.minimized:
            self.normal()

    def refresh(self) -> "Window":
        """Refresh window"""
        try:
            self.window.update()
        except Exception:
            pass
        return self

    def set_grab_anywhere(self, flag: bool) -> None:
        """Set grab anywhere"""
        self._grab_anywhere = flag
        if flag:
            self.window.bind("<B1-Motion>", self._move_window)
            self.window.bind("<ButtonPress-1>", self._start_move_window)
            self.window.bind("<ButtonRelease-1>", self._stop_move_window)
        else:
            self.window.unbind("<B1-Motion>")
            self.window.unbind("<ButtonPress-1>")
            self.window.unbind("<ButtonRelease-1>")
    
    def _move_window(self, event: tk.Event) -> None:
        """Move window"""
        if (not self._grab_anywhere) or (not self._grab_flag):
            return
        mouse_x = self.window.winfo_x() + event.x
        mouse_y = self.window.winfo_y() + event.y
        move_x = mouse_x - self._mouse_x
        move_y = mouse_y - self._mouse_y
        win_x = self._start_x + move_x
        win_y = self._start_y + move_y
        self.window.geometry(f"+{win_x}+{win_y}")

    def _start_move_window(self, event: tk.Event) -> None:
        """Start move window"""
        self._grab_flag = True
        loc = self.window.geometry().split("+")
        self._start_x = int(loc[1])
        self._start_y = int(loc[2])
        self._mouse_x = self.window.winfo_x() + event.x
        self._mouse_y = self.window.winfo_y() + event.y
    
    def _stop_move_window(self, event: tk.Event) -> None:
        """Stop move window"""
        self._grab_flag = False
    
    def bind(self, element: "Element", event_name: str, handle_name: str, propagate: bool=True, event_mode: EventMode = "user") -> None:
        """[Window.bind] Bind element event and handler"""
        element._bind_dict[event_name] = (handle_name, propagate, event_mode)
        if element.widget is None:
            return
        # bind to widget
        w: tk.Widget = element.widget
        w.bind(
            event_name,
            lambda e: _bind_event_handler(self, element, handle_name, e, propagate=propagate, event_mode=event_mode)
        )

    def set_icon(self, icon: Union[bytes, str]) -> None:
        """Set the icon for the window."""
        if isinstance(icon, str): # filename str
            icon = get_image_tk(filename=icon)
        if isinstance(icon, bytes):
            icon = tk.PhotoImage(data=icon)
        try:
            root = get_root_window()
            root.iconbitmap(self._icon)
        except Exception as e:
            print("Window.set_icon failed", file=sys.stderr)
            print(e, file=sys.stderr)

def _bind_event_handler(win: Window, elem: "Element", handle_name: str, event: tk.Event, propagate: bool=True, event_mode: EventMode = "user") -> None:
    """Handle an event."""
    elem.user_bind_event = event # for compatibility with PySimpleGUI
    if event_mode == "user":
        event_key = f"{elem.key}{handle_name}"
        event_val = {"event": event}
        win.events.put((event_key, event_val))
    elif event_mode == "system":
        event_key = elem.key
        event_val = {"event": event, "event_type": handle_name}
        for key, key_elem in win.key_elements.items():
            if key_elem.has_value:
                val = key_elem.get()
                event_val[key] = val
        win.events.put((event_key, event_val))
    # propagate
    if propagate:
        # todo
        pass

def _exit_mainloop() -> None:
    """Exit mainloop"""
    root = get_root_window()
    try:
        root.quit() # exit from mainloop
    except Exception:
        print("_exit_mainloop: failed to exit mainloop", file=sys.stderr)
        pass

def _focus_window(self: Window) -> None:
    """Focus window"""
    if not self.flag_alive:
        return
    if self.need_focus_widget is not None:
        self.need_focus_widget.focus_set()
        self.need_focus_widget = None
        _exit_mainloop()

#------------------------------------------------------------------------------
# Element
#------------------------------------------------------------------------------
# for compatibility with PySimpleGUI and etc
element_propery_alias: dict[str, str] = {
    "ButtonText": "text",
    "label": "text",
    "caption": "text",
    "justify": "text_align"
}
class Element:
    """Element class."""
    def __init__(
            self,
            element_type: str, # element type
            ttk_style_name: str, # tkinter widget type
            key: Union[str, None], # key
            has_value: bool, # has value
            metadata: Union[dict[str, Any], None] = None, # meta data
            **kw) -> None:
        """Create an element."""
        # define properties
        self.has_value: bool = has_value
        self.key: str|int|None = key
        if self.key is not None:
            register_element_key(self.key) # for checking unique key
        if self.has_value and (self.key is None or self.key == ""):
            self.key = generate_element_id()
        self.element_type: str = element_type
        self.ttk_style_name: str = ttk_style_name
        self.use_ttk: bool = False # use ttk style
        self.metadata = metadata
        self.style_name: str = self._generate_style_name(key)
        self.props: dict[str, Any] = kw
        self.widget: Any|None = None
        self.expand_x: bool = False
        self.expand_y: bool = False
        self.anchor: Union[str, None] = None
        self.has_children: bool = False
        self.prev_element: Element|None = None
        self.next_element: Element|None = None
        self.window: Window|None = None
        self.parent: tk.Widget|None = None
        self._bind_dict: dict[str, tuple[str, bool, EventMode]] = {}
        self.user_bind_event: tk.Event|None = None # when bind event fired then set this value
        self.vertical_alignment: TextVAlign = "center"
        self.text_align: TextAlign = "left"
        self.padx: int|tuple[int,int]|None = 1
        self.pady: int|tuple[int,int]|None = None
        self.font: Union[FontType, None] = None
        self.has_font_prop: bool = True
        self.col_no: int = -1
        self.row_no: int = -1
        self.disabled: bool = False

    def get_name(self) -> str:
        """Get key of element."""
        if self.key is None:
            return "-unknown-"
        return str(self.key)
    
    def get_width(self) -> int:
        """Get width of element."""
        if self.widget is None:
            return 0
        return self.widget.winfo_width()
    
    def get_height(self) -> int:
        """Get height of element."""
        if self.widget is None:
            return 0
        return self.widget.winfo_height()
    
    def bind(self, event_name: str, handle_name: str, propagate: bool=True, event_mode: EventMode = "user") -> None:
        """
        Bind event. @see [Window.bind](#windowbind)
        """
        self._bind_dict[event_name] = (handle_name, propagate, event_mode)
        if self.window is not None:
            self.window.bind(self, event_name, handle_name, propagate=propagate, event_mode=event_mode)

    def disptach_event(self, values: Union[dict[str, Any], None] = None) -> None:
        """Dispatch event"""
        if values is None:
            values = {}
        if self.window is not None:
            self.window._event_handler(self.key, values)
    
    def _justify_to_anchor(self, justify: TextAlign) -> str:
        """Convert justify to anchor"""
        if justify == "left":
            return "w"
        if justify == "right":
            return "e"
        return "center"

    def _set_pack_props(self,
                expand_x: Union[bool, None] = None,
                expand_y: Union[bool, None] = None,
                pad: PadType=None) ->None:
        """Set pack properties"""
        if expand_x is not None:
            self.expand_x = expand_x
        if expand_y is not None:
            self.expand_y = expand_y
        if pad is not None:
            if isinstance(pad, int):
                self.padx = self.pady = pad
            elif isinstance(pad, tuple):
                self.padx = pad[0]
                self.pady = pad[1]
            else:
                self.padx = pad[0][0]
                self.pady = pad[0][1]

    def _set_text_props(self,
                font: Union[FontType, None] = None,
                text_align: Union[TextAlign, None] = None,
                color: Union[str, None] = None,
                text_color: Union[str, None] = None,
                background_color: Union[str, None] = None) -> None:
        """set default props style"""
        if font is not None:
            self.props["font"] = font
            self.font = font
        if text_align is not None:
            self.props["justify"] = text_align
        if color is not None:
            self.props["fg"] = color
        if text_color is not None:
            self.props["fg"] = text_color
        if background_color is not None:
            self.props["bg"] = background_color

    def _get_pack_props(self, align: str="left", valign: str="top") -> dict[str, Any]:
        """Get the fill property in `pack` method."""
        props: dict[str, Any] = {"expand": False, "fill": "none", "side": "left"}
        if align == "right":
            props["side"] = "right"
        elif align == "center":
            props["fill"] = "both"
            props["expand"] = True
        # check expand
        if self.expand_x and self.expand_y:
            props["expand"] = True
            props["fill"] = "both"
        elif self.expand_x:
            props["expand"] = True
            props["fill"] = "x"
        elif self.expand_y:
            props["expand"] = True
            props["fill"] = "y"
        # padx / pady
        if self.padx is not None:
            props["padx"] = self.padx
        if self.pady is not None:
            props["pady"] = self.pady
        # anchor
        if self.anchor is not None:
            props["anchor"] = self.anchor
        return props

    def _convert_props(self, props: dict[str, Any]) -> dict[str, Any]:
        result = {}
        # copy
        for key, val in props.items():
            result[key] = val
        # check props
        # size
        if "size" in result:
            size = result.pop("size", (8, 1))
            result["width"] = size[0]
            result["height"] = size[1]
        # background_color
        if "background_color" in result:
            result["bg"] = result.pop("background_color")
        if "text_color" in result:
            result["fg"] = result.pop("text_color")
        if "color" in result:
            result["fg"] = result.pop("color")
        # expand_x
        if "expand_x" in result:
            self.expand_x = result.pop("expand_x")
        if "expand_y" in result:
            self.expand_y = result.pop("expand_y")
        # padx / pady
        if "padx" in result:
            self.padx = result.pop("padx")
        if "pady" in result:
            self.pady = result.pop("pady")
        # anchor
        if "anchor" in result:
            self.anchor = result.pop("anchor")
        # convert "select_mode" to "selectmode"
        if "select_mode" in result:
            result["selectmode"] = result.pop("select_mode")
        # user bind events
        if "bind_events" in result:
            bind_events = result.pop("bind_events")
            self.bind_events(bind_events)
        # disabled
        if "disabled" in result:
            result["state"] = tk.DISABLED if result.pop("disabled") else tk.NORMAL
        return result

    def set_disabled(self, disabled: bool) -> None:
        """
        Set disabled widgets state
        """
        self.disabled = disabled
        state = tk.DISABLED if disabled else tk.NORMAL
        self._widget_update(state=state)

    def bind_events(self, events: dict[str, str], event_mode: EventMode="user") -> Element:
        """
        Bind user events. @see [custom events](/docs/custom_events.md)
        The specification is such that if the suffix "/hide" is attached to an event key, that event key will not be returned to the user.
        @see [Window.read](#windowread)
        """
        for event_name, handle_name in events.items():
            self.bind(event_name, handle_name, event_mode=event_mode)
        return self

    def create(self, win: Window, parent: tk.Widget) -> Any:
        """Create a widget."""
        return None

    def prepare_create(self, win: Window) -> None:
        # convert properties
        if (win.font is not None) and (self.font is None) and self.has_font_prop:
            self.props["font"] = self.font = win.font
        self.props = self._convert_props(self.props)
        # check use ttk
        if not self.use_ttk:
            return
        # set style
        style = get_ttk_style()
        style_name = self.style_name
        # create style
        if style_name not in style.element_names():
            style.element_create(style_name, "from", get_current_theme())
        # set font style
        font = None
        if "font" in self.props:
            font = self.props.pop("font")
            style.configure(style_name, font=font)
        # fg / bg
        if "fg" in self.props:
            fg = self.props.pop("fg")
            style.configure(style_name, foreground=fg)
            if self.ttk_style_name == "TLabelframe":
                style.configure(f"{style_name}.Label", foreground=fg)
        if "bg" in self.props:
            bg = self.props.pop("bg")
            style.configure(style_name, background=bg)
            if self.ttk_style_name == "TLabelframe":
                style.configure(f"{style_name}.Label", background=bg)
        # set readonlybackground
        if "readonlybackground" in self.props:
            readonlybackground = self.props.pop("readonlybackground")
            style.map(style_name, background=[("readonly", readonlybackground)])
        # check element type
        # Button ?
        if self.ttk_style_name == "TButton" or self.ttk_style_name == "TLabel":
            if "justify" in self.props:
                anchor = self._justify_to_anchor(self.props.pop("justify"))
                style.configure(style_name, anchor=anchor)
            if "height" in self.props:
                height = self.props.pop("height")
                self.pady = (height-1)//2
    
    def _generate_style_name(self, style_key: Union[str, None]) -> str:
        """generate style name"""
        if style_key is None or style_key == "":
            style_key = generate_element_style_key(self.element_type)
        if "." in self.ttk_style_name:
            return f"{self.ttk_style_name}"
        else:
            return f"{style_key}.{self.ttk_style_name}"


    def post_create(self, win: Window, parent: tk.Widget) -> None:
        """Post create widget."""
        pass

    def get(self) -> Any:
        """Get the value of the widget."""
        return "-"
    
    def update(self, *args, **kw) -> None:
        """update widget configuration."""
        pass
    
    def _widget_update(self, **kw) -> None:
        # update element's props
        for k, v in kw.items():
            self.props[k] = v
        kw = self._convert_props(kw)
        try:
            if (self.widget is not None)and(len(kw) > 0):
                self.widget.configure(**kw)
        except Exception as e:
            print(f"TkEasyGUI.Element._widget_update.Error: key='{self.key}', props={kw}. {e}", file=sys.stderr)

    def get_prev_widget(self, target_key: Union[str, None] = None) -> tk.Widget:
        """Get the previous widget."""
        # check target_key
        target: tk.Widget = None
        if target_key:
            if target_key in self.window.key_elements:
                target = self.window.key_elements[target_key]
                return target
        # get prev_widget
        return self.prev_element

    def __getattr__(self, name: str) -> Any:
        """Get unknown attribute."""
        # Method called when the attribute is not found in the object's instance dictionary
        if self.widget is not None:
            # Widget
            if name == "Widget": # for compatibility with PySimpleGUI
                return self.widget
            # prop
            if hasattr(self.widget, name):
                return self.widget.__getattribute__(name)
        return self.__getitem__(name)

    def __getitem__(self, name: str) -> Any:
        """Get element property"""
        # For compatibility with PySImpleGUI
        if name in element_propery_alias:
            name = element_propery_alias[name]
        # check self.props
        if name in self.props:
            return self.props[name]
        # check widget native property
        if self.widget is not None:
            if name in self.widget:
                return self.widget[name]
        return None

class Frame(Element):
    """Frame element."""
    def __init__(
        self,
        title: str,
        layout: list[list[Element]],
        key: str = "",
        size: Union[tuple[int, int], None] = None,
        relief: ReliefType = "groove",
        # text props
        font: Union[FontType, None] = None,  # font
        color: Union[str, None] = None,
        text_color: Union[str, None] = None,
        background_color: Union[str, None] = None,  # background_color
        # pack props
        label_outside: bool = False,
        vertical_alignment: TextVAlign = "top",  # vertical alignment
        text_align: Union[TextAlign, None] = "left",  # text align
        # pack props
        expand_x: bool = False,
        expand_y: bool = False,
        pad: Union[PadType, None] = None,
        # other
        metadata: Union[dict[str, Any], None] = None,
        use_ttk: bool = False,
        **kw,
    ) -> None:
        style_name = "TLabelframe" if use_ttk else ""
        super().__init__("Frame", style_name, key, False, metadata, **kw)
        self.has_children = True
        self.layout = layout
        self.label_outside = label_outside
        self.props["text"] = title
        self.props["relief"] = relief
        self.text_align = text_align
        self.vertical_alignment = vertical_alignment
        self._set_text_props(color=color, text_color=text_color, background_color=background_color, font=font)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        self.use_ttk: bool = use_ttk
        if size is not None:
            self.props["size"] = size

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Frame widget."""
        if self.use_ttk:
            get_ttk_style().configure(self.style_name, labeloutside=self.label_outside)
            self.widget = ttk.LabelFrame(
                parent,
                style=self.style_name,
                **self.props)
        else:
            # dfault
            self.widget = tk.LabelFrame(parent, **self.props)
        return self.widget

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)
    
    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget"]:
            return self.widget
        return super().__getattr__(name)

class Column(Element):
    """Frame element."""
    def __init__(
                self,
                layout: list[list[Element]],
                key: str = "",
                background_color: Union[str, None] = None,
                vertical_alignment: TextVAlign="top",
                size: Union[tuple[int, int], None] = None, # set (width, height) pixel size
                width: Union[int, None] = None, # set pixel width
                # text props
                text_align: Union[TextAlign, None]="left", # text align
                # pack props
                expand_x: bool = False,
                expand_y: bool = False,
                pad: Union[PadType, None] = None,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("Column", "TFrame", key, False, metadata, **kw)
        self.has_children = True
        self.layout = layout
        self.text_align = text_align
        self.vertical_alignment = vertical_alignment
        self.has_font_prop = False
        self.use_ttk = False
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        self.size = size
        if width is not None:
            self.size = (width, 400)
        if self.size is not None:
            self.props["size"] = self.size
        if background_color is not None:
            self.props["background_color"] = background_color
        if text_align is not None:
            self.props["anchor"] = self._justify_to_anchor(text_align)

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        # if self.use_ttk:
        #     self.widget = ttk.Frame(parent, style=self.style_name, **self.props)
        self.widget: tk.Frame = tk.Frame(parent, **self.props)
        if self.size is not None:
            self.widget.pack_propagate(False)
        return self.widget

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)
    
    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget"]:
            return self.widget
        return super().__getattr__(name)

class Tab(Element):
    """
    (experimental) Tab element - Tab is used together with TabGroup.
    **Example:**
    ```py
    import TkEasyGUI as sg
    # Tab's Layout
    tab1_layout = [[sg.Text("Tab1")], [sg.Input(key="input1")], [sg.Button("Read1")]]
    tab2_layout = [[sg.Text("Tab2")], [sg.Input(key="input2")], [sg.Button("Read2")]]
    # Main Layout
    layout = [[
        sg.TabGroup([[
            sg.Tab("Tab title1", tab1_layout),
            sg.Tab("Tab title2", tab2_layout),
        ]])],
        [sg.Button("Quit")]]
    # create window and event loop
    with sg.Window("Tab Demo", layout) as window:
        for event, values in window:
            pass
    ```
    """
    def __init__(
        self,
        title: str,
        layout: list[list[Element]],
        key: str = "",
        background_color: Union[str, None] = None,
        vertical_alignment: TextVAlign = "top",
        size: Union[tuple[int, int], None] = None,
        # text props
        text_align: Union[TextAlign, None] = "left",  # text align
        # pack props
        expand_x: bool = False,
        expand_y: bool = False,
        pad: Union[PadType, None] = None,
        # other
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("Tab", "Frame", key, False, metadata, **kw)
        self.has_children = True
        self.title = title
        self.layout = layout
        self.text_align = text_align
        self.vertical_alignment = vertical_alignment
        self.has_font_prop = False
        self.use_ttk = False
        self.rows = len(layout)
        self.cols = 0
        for row in layout:
            self.cols = max(self.cols, len(row))
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        if size is not None:
            self.props["size"] = size
        if background_color is not None:
            self.props["background_color"] = background_color
        if text_align is not None:
            self.props["anchor"] = self._justify_to_anchor(text_align)

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.widget = tk.Frame(parent, **self.props)
        return self.widget

    def get(self) -> Any:
        """Return Widget title"""
        return self.title

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)

    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget"]:
            return self.widget
        return super().__getattr__(name)


class TabGroup(Element):
    """
    (experimental) TabGroup element - Specify the Tab element for the child elements.

    **Example:**
    ```py
    import TkEasyGUI as sg
    # Tab's Layout
    tab1_layout = [[sg.Text("Tab1")], [sg.Input(key="input1")], [sg.Button("Read1")]]
    tab2_layout = [[sg.Text("Tab2")], [sg.Input(key="input2")], [sg.Button("Read2")]]
    # Main Layout
    layout = [[
        sg.TabGroup([[
            sg.Tab("Tab title1", tab1_layout),
            sg.Tab("Tab title2", tab2_layout),
        ]])],
        [sg.Button("Quit")]]
    # create window and event loop
    with sg.Window("Tab Demo", layout) as window:
        for event, values in window:
            pass
    ```
    """
    def __init__(
        self,
        layout: Union[list[list["TabGroup"]], list["TabGroup"]],
        key: str = "",
        background_color: Union[str, None] = None,
        vertical_alignment: TextVAlign = "top",
        size: Union[tuple[int, int], None] = None,
        # text props
        text_align: Union[TextAlign, None] = "left",  # text align
        # pack props
        expand_x: bool = True,
        expand_y: bool = True,
        pad: Union[PadType, None] = None,
        # other
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("TabGroup", "Notebook", key, False, metadata, **kw)
        self.has_children = True
        # check layout type
        if layout is None:
            layout = []
        if len(layout) > 0:
            if not isinstance(layout[0], list):
                layout = [layout]
            if not isinstance(layout[0][0], Tab):
                raise ValueError("TabGroup layout should be list of Tab")
        self.layout = layout
        self.text_align = text_align
        self.vertical_alignment = vertical_alignment
        self.has_font_prop = False
        self.use_ttk = True
        self.background_color = background_color
        self.max_rows = 3
        self.max_cols = 3
        self.window = None
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        if text_align is not None:
            self.props["anchor"] = self._justify_to_anchor(text_align)

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.window = win
        self.widget = ttk.Notebook(parent, **self.props)
        return self.widget
    
    def post_create(self, win: Window, parent: tk.Widget) -> None:
        if win.size is None:
            win.set_size((600, 400))
        return super().post_create(win, parent)

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)

    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget"]:
            return self.widget
        return super().__getattr__(name)



class Text(Element):
    """Text element."""
    def __init__(
                self,
                text: str = "",
                key: Union[str, None] = None,
                enable_events: bool=False, # enabled events (click)
                wrap_length: Union[int, None] = None, # wrap length(unit=pixel)
                # text props
                text_align: Union[TextAlign, None]="left", # text align
                font: Union[FontType, None] = None, # font
                color: Union[str, None] = None, # text color
                text_color: Union[str, None] = None, # same as color
                background_color: Union[str, None] = None, # background color
                # pack props
                expand_x: bool = False,
                expand_y: bool = False,
                pad: Union[PadType, None] = None,
                # other
                metadata: Union[dict[str, Any], None] = None, # user metadata
                **kw
                ) -> None:
        key = text if (key is None) or (key == "") else key
        super().__init__("Text", "", key, False, metadata, **kw)
        self.props["text"] = text
        self._set_text_props(font=font, text_align=text_align, color=color, text_color=text_color, background_color=background_color)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        self.enable_events = enable_events
        if wrap_length is not None:
            self.props["wraplength"] = wrap_length

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Text widget."""
        if "justify" in self.props:
            val = self.props.pop("justify")
            self.props["anchor"] = self._justify_to_anchor(val)
            self.props["justify"] = val
        self.widget = tk.Label(parent, **self.props)
        if self.enable_events:
            self.widget.bind("<Button-1>", lambda e: self.disptach_event({"event_type": "click", "event": e}))
        return self.widget
    
    def get(self) -> Any:
        """Get the value of the widget."""
        return self.get_text()
    
    def get_text(self) -> str:
        return self.props["text"]
    
    def set_text(self, text: str) -> None:
        """Set the text of the widget."""
        self.props["text"] = text
        self._widget_update(text=text)

    def update(self, text: Union[str, None] = None, *args, **kw) -> None:
        """Update the widget."""
        if text is not None:
            self.set_text(text)
        self._widget_update(**kw)

class Label(Text):
    """
    Label element (alias of Text)
    """
    pass

class Menu(Element):
    """
    Menu element.
    **Example**
    ```
    menu = eg.Menu([
        ["File", ["Open", "Save", "---","Exit"]],
        ["Edit", ["Copy", "Paste"]],
    ])
    ```
    **Note**
    - "!label" is disabled
    - "label::-event_name-" is set event name
    - "---" is separator
    """
    def __init__(
                self,
                items: Union[Any, None] = None,
                menu_definition: Union[list[list[Union[str,list[Any]]]], None] = None,
                key: Union[str, None] = None,
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("Menu", "", key, False, metadata, **kw)
        self.items = menu_definition
        if items is not None:
            self.items = items
    
    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Text widget."""
        self.widget = tk.Menu(win.window)
        win.window.config(menu=self.widget)
        # make items
        self._create_menu(self.widget, self.items, 0)
        return self.widget
    
    def _add_command(self, parent: tk.Menu, label: str) -> None:
        # is separator?
        if label == "-" or label == "---":
            parent.add_separator()
            return
        # command
        key = label
        state = tk.NORMAL
        if label.startswith("!"):
            label = label[1:]
            state = tk.DISABLED
        if "::" in label:
            label, key = label.split("::")
        parent.add_command(
            label=label, 
            state=state,
            command=lambda : self.disptach_event({EG_SWAP_EVENT_NAME: key}))

    def _create_menu(self, parent: tk.Menu, items: list[list[Union[str, list[Any]]]], level:int = 0) -> None:
        i = 0
        while i < len(items):
            item = items[i]
            if isinstance(item, int) or isinstance(item, float):
                item = str(item)
            if isinstance(item, str):
                # check next item
                next_item = items[i+1] if i+1 < len(items) else None
                if (next_item is None) or (not isinstance(next_item, list)):
                    self._add_command(parent, item)
                    i += 1
                    continue
                else: # if isinstance(next_item, list):
                    # submenu
                    submenu = tk.Menu(parent, tearoff=False)
                    parent.add_cascade(label=item, menu=submenu)
                    self._create_menu(submenu, next_item, level+1)
                    i += 2
                    continue
            if isinstance(item, list):
                self._create_menu(parent, item, level+1)
                i += 1
                continue
            # others
            i += 1

    def get(self) -> Any:
        """Get the value of the widget."""
        return self.get_text()
    
    def get_text(self) -> str:
        return self.props["text"]
    
    def set_text(self, text: str) -> None:
        """Set the text of the widget."""
        self.props["text"] = text
        self._widget_update(text=text)

    def update(self, text: Union[str, None] = None, *args, **kw) -> None:
        """Update the widget."""
        if text is not None:
            self.set_text(text)
        self._widget_update(**kw)

class Button(Element):
    """
        Button element

        **Example**
        The program below changes the button's label to "Pushed" when the button is pressed.
        ```python
        import TkEasyGUI as eg
        button:eg.Button = eg.Button("Push me")
        with eg.Window("Title", layout=[[button]]) as window:
            for event, values in window.event_iter():
                if event == button.get_text():
                    button.set_text("Pushed")
                    break
        ```
    """
    def __init__(
        self,
        button_text: str = "Button",
        key: Union[str, None] = None,
        disabled: bool = False,
        size: Union[tuple[int, int], None] = None,
        tooltip: Union[str, None] = None,  # (TODO) tooltip
        button_color: Union[str, tuple[str, str], None] = None,
        # text props
        text_align: Union[TextAlign, None] = "left",  # text align
        font: Union[FontType, None] = None,  # font
        color: Union[str, None] = None,  # text color
        text_color: Union[str, None] = None,  # same as color
        background_color: Union[str, None] = None,  # background color (not supported on macOS)
        # pack props
        expand_x: bool = False,
        expand_y: bool = False,
        pad: Union[PadType, None] = None,
        # other
        use_ttk_buttons: bool = False,
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        key = button_text if (key is None) or (key == "") else key
        super().__init__("Button", "TButton", key, False, metadata, **kw)
        self.use_ttk = use_ttk_buttons # can select ttk or tk button
        self.disabled = False
        if disabled is not None:
            self.props["disabled"] = self.disabled = disabled
        if size is not None:
            self.props["size"] = size
        self.props["text"] = button_text
        self.tooltip: Union[str,None] = tooltip
        if button_color is not None:
            self.set_button_color(button_color, update=False)
        self._set_text_props(font=font, text_align=text_align, color=color, text_color=text_color, background_color=background_color)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        self.bind_events({
            "<Button-3>": "right_click",
            "<Return>": "return",
        }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Button widget."""
        if self.use_ttk:
            self.widget = ttk.Button(
                parent,
                command=lambda: self.disptach_event({"event_type": "command"}),
                **self.props)
        else:
            self.widget = tk.Button(
                parent,
                command=lambda: self.disptach_event({"event_type": "command"}),
                **self.props)
        return self.widget

    def set_button_color(self, button_color: Union[str, tuple[str,str]], update: bool = True) -> None:
        """Set the button color."""
        props = {}
        if isinstance(button_color, tuple):
            if len(button_color) == 2:
                props["text_color"] = button_color[0]
                props["background_color"] = button_color[1]
            elif len(button_color) == 1:
                props["background_color"] = button_color[0]
        else:
            props["background_color"] = button_color
        if update:
            self._widget_update(props)

    def get(self) -> Any:
        """Returns the text of the button.."""
        return self.get_text()
    
    def set_text(self, text: str) -> None:
        """Set the text of the button."""
        self.props["text"] = text
        self._widget_update(text=text)
    
    def get_text(self) -> str:
        """Get the text of the button."""
        return self.props["text"]

    def update(self,
               text: Union[str, None] = None, 
               disabled: Union[bool, None] = None,
               button_color: Union[str, tuple[str,str], None] = None,
               **kw) -> None:
        """Update the widget."""
        if text is not None:
            self.props["text"] = text
            self._widget_update(text=text)
        if disabled is not None:
            self.set_disabled(disabled)
        if button_color is not None:
            self.set_button_color(button_color, update=False)
        # other
        self._widget_update(**kw)
    
    def __getattr__(self, name: str) -> Any:
        """Get unknown attribute. """
        # Get the text of the button. (compatibility with PySimpleGUI)
        if name == "GetText":
            return self.get_text
        elif name == "ButtonText":
            return self.get_text()
        return super().__getattr__(name)

class CloseButton(Button):
    """CloseButton element."""
    def __init__(
        self,
        button_text: str = "Close",
        key: Union[str, None] = None,
        **kw,
    ) -> None:
        key = button_text if (key is None) or (key == "") else key
        super().__init__(button_text=button_text, key=key, **kw)

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Button widget."""
        super().create(win, parent)
        win.register_event_hooks({
            self.key: [
                lambda _event, _value: self.close_window()
            ]
        })
        return self.widget
    
    def close_window(self) -> None:
        """Close the window."""
        self.window.close()

class Submit(Button):
    """Subtmi element. (Alias of Button) : todo: add submit event"""
    pass

class Checkbox(Element):
    """Checkbox element."""
    def __init__(
                self, text: str="",
                default: bool=False,
                key: Union[str, None] = None,
                enable_events: bool=False,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        if key is None or key == "":
            key = text
        super().__init__("Checkbox", "TCheckbutton", key, True, metadata, **kw)
        self.use_ttk = True
        self.default_value = default
        self.props["text"] = text
        if enable_events:
            self.bind_events({
                "<Button-3>": "right_click"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.checkbox_var = tk.BooleanVar(value=self.default_value)
        self.checkbox_var.trace_add("write", lambda *args: self.disptach_event({"event_type": "change", "event": args}))
        self.widget = ttk.Checkbutton(parent, style=self.style_name, variable=self.checkbox_var, **self.props)
        return self.widget
    
    def get_value(self) -> Any:
        """Get the value of the widget."""
        return self.checkbox_var.get()

    def set_value(self, b: bool) -> None:
        """Set the value of the widget."""
        self.checkbox_var.set(b)

    def get(self) -> Any:
        """Get the value of the widget."""
        return self.get_value()

    def set_text(self, text: str) -> None:
        """Set the text of the widget."""
        self.props["text"] = text
        self._widget_update(text=text)

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        if len(args) >= 1:
            self.set_value(args[0])
        if len(args) >= 2:
            self.set_text(args[1])
        if "text" in kw:
            self.set_text(kw.pop("text"))
        if "value" in kw:
            self.set_value(kw.pop("value"))
        self._widget_update(**kw)

class Radio(Element):
    """Checkbox element."""
    def __init__(
                self, text: str="",
                group_id: Union[int, str] = "group",
                default: bool = False,
                key: Union[str, None] = None,
                enable_events: bool = False,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        if key is None or key == "":
            key = text
        super().__init__("Radio", "TRadiobutton", key, True, metadata, **kw)
        self.use_ttk = True
        self.default_value = default
        self.value: int = 0
        self.props["text"] = text
        self.group_id: str = str(group_id)
        if enable_events:
            self.bind_events({
                "<Button-3>": "right_click"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        # create radio group
        if self.group_id not in win.radio_group_dict:
            win.radio_group_dict[self.group_id] = [tk.IntVar(value=0), 1]
            win.radio_group_dict[self.group_id][0].trace_add("write", lambda *args: self.disptach_event({"event_type": "change", "event": args}))
        else:
            win.radio_group_dict[self.group_id][1] += 1
        self.value = win.radio_group_dict[self.group_id][1]
        # create radiobutton
        self.widget = ttk.Radiobutton(
            parent,
            value=self.value,
            variable=win.radio_group_dict[self.group_id][0],
            style=self.style_name,
            **self.props)
        if self.default_value:
            self.select()
        return self.widget
    
    def select(self) -> None:
        """Select the radio button."""
        self.window.radio_group_dict[self.group_id][0].set(self.value)
    
    def is_selected(self) -> bool:
        """Check if the radio button is selected."""
        return self.window.radio_group_dict[self.group_id][0].get() == self.value

    def get_value(self) -> bool:
        """Get the value of the widget."""
        return self.value

    def get(self) -> Any:
        """Get the value of the widget."""
        return self.is_selected()

    def set_text(self, text: str) -> None:
        """Set the text of the widget."""
        self.props["text"] = text
        self._widget_update(text=text)

    def update(self, text: Union[str, None] = None, **kw) -> None:
        """Update the widget."""
        if text is not None:
            self.set_text(text)
        self._widget_update(**kw)

class Input(Element):
    """
    Text input element.
    """
    def __init__(
                self,
                text: str = "", # default text
                key: Union[str, None] = None, # key
                default_text: Union[str, None] = None, # same as text
                enable_events: bool = False, # enabled events ([enter] or [change])
                enable_key_events: bool = False,  # enabled key events
                enable_focus_events: bool = False, # enabled focus events
                readonly_background_color: Union[str, None] = "silver",
                password_char: Union[str, None] = None, # if you want to use it as a password input box, set "*"
                readonly: bool = False, # read only box
                size: Union[tuple[int, int], None] = None, # set (width, height) character size (only width is supported)
                width: Union[int, None] = None, # set width character size
                # text props
                text_align: Union[TextAlign, None] = "left", # text align
                font: Union[FontType, None] = None, # font
                color: Union[str, None] = None, # text color
                text_color: Union[str, None] = None, # same as color
                background_color: Union[str, None] = None, # background color
                # pack props
                expand_x: bool = False,
                expand_y: bool = False,
                pad: Union[PadType, None] = None,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        super().__init__("Input", "TEntry", key, True, metadata, **kw)
        self.use_ttk = False
        self.readonly: bool = readonly
        self.enable_events: bool = enable_events
        if default_text is not None: # compatibility with PySimpleGUI
            text = default_text
        self.default_text = text # default text @see Input.create
        self._set_text_props(font=font, text_align=text_align, color=color, text_color=text_color, background_color=background_color)
        if readonly_background_color is not None:
            self.props["readonlybackground"] = readonly_background_color
        if password_char is not None:
            self.props["show"] = password_char
        if size is not None:
            self.props["size"] = size
        if width is not None:
            self.props["size"] = (width, 1)
        # set props
        self._set_text_props(font=font, text_align=text_align, color=color, text_color=text_color, background_color=background_color)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        if enable_events:
            self.bind_events({
                "<Return>": "return",
            }, "system")
        if enable_key_events:
            self.bind_events({
                "<Key>": "key",
            }, "system")
        if enable_focus_events:
            self.bind_events({
                "<FocusIn>": "focusin",
                "<FocusOut>": "focusout",
                "<Button-1>": "click",
                "<Button-3>": "right_click"
            }, "system")
    
    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """create Input widget"""
        # check props
        # if "height" in self.props:
        #     self.props.pop("height") # no property
        # set default text
        self.text_var = tk.StringVar(value=self.default_text)
        if "height" in self.props:
            self.props.pop("height")
        # create
        self.widget = tk.Entry(
            parent,
            textvariable=self.text_var,
            # style=self.style_name,
            **self.props)
        # set readonly
        if self.readonly:
            self.set_readonly(self.readonly)
        # trace change
        if self.enable_events:
            self.text_var.trace_add("write",
                lambda *args: self.disptach_event({"event_type": "change", "event": args}))
        return self.widget

    def get(self) -> Any:
        """Get the value of the widget."""
        return self.get_text()
    
    def set_text(self, text: str) -> None:
        """set text"""
        if self.widget is None:
            return
        # change text
        self.widget.config(textvariable=self.text_var)
        self.text_var.set(text)
        #  OR
        #   self.delete(0, "end")
        #   self.insert(0, text)

    def get_text(self) -> str:
        """get text"""
        return self.text_var.get()
    
    def get_selected_text(self) -> str:
        """get selected text"""
        if self.widget is None:
            return ""
        try:
            return self.widget.selection_get()
        except Exception:
            return ""

    def copy_selected_text(self) -> None:
        """Copy selected text"""
        text = self.get_selected_text()
        utils.set_clipboard(text)

    def set_readonly(self, readonly: bool) -> None:
        """set readonly"""
        self.readonly = readonly
        state = "readonly" if self.readonly else "normal"
        self._widget_update(state=state)

    def update(self, text: Union[str, None] = None, readonly: Union[bool, None] = None, **kw) -> None:
        """Update the widget."""
        if self.widget is None:
            return
        # check readonly
        if readonly is not None:
            self.set_readonly(readonly)
        # text
        if text is not None:
            if self.readonly:
                self.set_readonly(False)
                self.set_text(text)
                self.set_readonly(True)
            else:
                self.set_text(text)
        # update others
        self._widget_update(**kw)
    
    def select_all(self) -> None:
        """select_all"""
        if self.widget is None:
            return
        input: tk.Entry = self.widget
        input.select_range(0, "end")
        input.icursor("end")
    
    def copy(self) -> str:
        """copy to clipboard"""
        if self.widget is None:
            return
        text = self.get_selected_text()
        utils.set_clipboard(text)
        return text

    def cut(self) -> str:
        """cut to clipboard"""
        if self.widget is None:
            return
        self.copy()
        return self.delete_selected()
    
    def delete_selected(self) -> str:
        """delete selected text"""
        if self.widget is None:
            return
        try:
            text = self.get_selected_text()
            self.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception as _:
            return ""
        return text

    def paste(self):
        """paste from clipboard"""
        if self.widget is None:
            return
        # delete selected
        self.delete_selected()
        # insert
        text = utils.get_clipboard()
        input: tk.Entry = self.widget
        current_cursor_position = input.index(tk.INSERT)
        input.insert(current_cursor_position, text)
    
    def get_selection_pos(self) -> tuple[int, int]:
        """get selection positions"""
        try:
            entry: tk.Entry = self.widget
            start_pos = entry.index(tk.SEL_FIRST)
            end_pos = entry.index(tk.SEL_LAST)
            return start_pos, end_pos
        except Exception as _:
            cur = self.get_cursor_pos()
            return [cur, cur]
    
    def get_cursor_pos(self) -> int:
        """get cursor position"""
        cursor_pos = self.widget.index(tk.INSERT)
        return cursor_pos

    def set_cursor_pos(self, index: int) -> None:
        """set cursor position"""
        self.widget.icursor(index)
 
    def get_selection_start(self) -> int:
        """get selection start"""
        try:
            entry: tk.Entry = self.widget
            start_pos = entry.index(tk.SEL_FIRST)
            return start_pos
        except Exception as _:
            return self.get_cursor_pos()

    def get_selection_length(self) -> tuple[int, int]:
        """get selection length"""
        try:
            entry: tk.Entry = self.widget
            start_pos = entry.index(tk.SEL_FIRST)
            end_pos = entry.index(tk.SEL_LAST)
            return end_pos - start_pos
        except Exception as _:
            return 0
    
    def set_selection_start(self, sel_start: int, sel_length: int=0) -> None:
        """set selection start and length"""
        try:
            entry: tk.Entry = self.widget
            sel_end = sel_start + sel_length
            entry.selection_range(sel_start, sel_end)
        except Exception as _:
            pass

class InputText(Input):
    """InputText element. (alias of Input)"""
    pass

class Multiline(Element):
    """Multiline text input element."""
    def __init__(
        self,
        text: str = "",  # default text
        default_text: Union[str, None] = None,  # same as text
        key: Union[str, None] = None,  # key
        readonly: bool = False,
        enable_events: bool = False,
        enable_key_events: bool = False,
        enable_focus_events: bool = False,
        size: tuple[int, int] = (50, 10),  # element size (unit=character)
        # text props
        font: Union[FontType, None] = None,  # font
        color: Union[str, None] = None,  # text color
        text_color: Union[str, None] = None,  # same as color
        background_color: Union[str, None] = None,  # background color
        text_align: Union[TextAlign, None] = None,  # text align
        # pack props
        expand_x: bool = False,
        expand_y: bool = False,
        pad: Union[PadType, None] = None,
        # other
        autoscroll: bool = False, # When autoscroll is set to True, it scrolls to the end with text changes.
        readonly_background_color: Union[str, None] = None,
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("Multiline", "", key, True, metadata, **kw)
        if default_text is not None:
            text = default_text
        self.props["text"] = text
        self.props["size"] = size
        self._set_text_props(font=font, color=color, text_color=text_color, background_color=background_color)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        self.text_align = text_align
        if readonly_background_color is not None:
            self.readonly_background_color = readonly_background_color
        self.has_value = True
        self.readonly = readonly
        self.autoscroll = autoscroll
        # bind events
        if enable_events:
            self.bind_events({
                "<Return>": "return",
            }, "system")
        if enable_key_events:
            self.bind_events({
                "<Key>": "key",
            }, "system")
        if enable_focus_events:
            self.bind_events({
                "<FocusIn>": "focusin",
                "<FocusOut>": "focusout",
                "<Button-1>": "click",
                "<Button-3>": "right_click"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Multiline widget."""
        # text
        text = self.props.pop("text", "")
        # create
        self.widget: scrolledtext.ScrolledText = scrolledtext.ScrolledText(parent, **self.props)
        # text_align
        if self.text_align is not None:
            self.widget.tag_configure(self.text_align, justify=self.text_align)
            self.widget.insert("1.0", text, self.text_align)
        else:
            # set text
            self.widget.insert("1.0", text)
        # readonly
        if self.readonly:
            self.set_readonly(self.readonly)
        # event_hook
        if (self.text_align is not None) and (self.text_align != "left"):
            hook_event_key = "--text_align_return/hide"
            self.bind_events({"<Return>": hook_event_key})
            win.register_event_hooks({
                f"{self.key}{hook_event_key}": [ self._hook_return_event_for_text_align ]
            })
        return self.widget
    
    def _hook_return_event_for_text_align(self, event, values) -> None:
        """Hook Return key event for text_align."""
        if event == f"{self.key}--text_align_return/hide": # @see Multiline.create > event_hook
            text = self.get_text()
            self.set_text(text)

    def get(self) -> Any:
        """Get the value of the widget."""
        if self.widget is None:
            return ""
        return self.get_text()
    
    def get_text(self) -> str:
        """Get the text of the widget."""
        if self.widget is None:
            return ""
        text = self.widget.get("1.0", "end -1c") # get all text
        return text
    
    def get_selected_text(self) -> str:
        """Get the selected text."""
        if self.widget is None:
            return ""
        try:
            text = self.widget.selection_get()
        except Exception:
            text = ""
        return text
    
    def copy(self) -> str:
        """Copy the selected text."""
        if self.widget is None:
            return
        text = self.get_selected_text()
        utils.set_clipboard(text)
        return text
    
    def paste(self) -> None:
        """Paste the text."""
        if self.widget is None:
            return
        text = utils.get_clipboard()
        self.widget.insert(tk.INSERT, text)
        self.widget.tag_remove(tk.SEL, '1.0', tk.END) 
        self.widget.see(tk.INSERT)

    def cut(self) -> str:
        """Cut the selected text."""
        if self.widget is None:
            return
        text = ""
        if self.widget.tag_ranges(tk.SEL):
            text = self.copy()
            self.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        return text

    def update(
        self,
        text: Union[str, None] = None,
        readonly: Union[bool, None] = None,
        autoscroll: Union[bool, None] = None,  # When autoscroll is set to True, it scrolls to the end with text changes.
        **kw,
        ) -> None:
        """Update the widget."""
        if autoscroll is not None:
            self.autoscroll = autoscroll
        if text is not None:
            self.set_text(text)
        if readonly is not None:
            self.set_readonly(readonly)
        self._widget_update(**kw)

    def set_readonly(self, readonly: bool) -> None:
        """Set readonly"""
        self.readonly = readonly
        state = tk.DISABLED if readonly else tk.NORMAL
        self._widget_update(state=state)

    def set_text(self, text: str) -> None:
        """Set text"""
        if self.widget is None:
            return
        if self.readonly:
            self._widget_update(state=tk.NORMAL)
        self.props["text"] = text
        # clear text
        self.widget.delete("1.0", "end") # clear text
        # set text
        if self.text_align is not None:
           self.widget.insert("1.0", text, self.text_align)
        else:
            self.widget.insert("1.0", text)
        if self.readonly:
            self._widget_update(state=tk.DISABLED)
        # autoscroll ?
        if self.autoscroll:
            self.widget.see(tk.END)
    
    def get_selection_pos(self) -> tuple[str, str]:
        """Get selection position, returns (start_pos, end_pos)."""
        if self.widget is None:
            return ("", "")
        try:
            sel_start, sel_end = self.widget.tag_ranges("sel")
            return (sel_start, sel_end)
        except Exception as _:
            pos = self.get_cursor_pos()
            return (pos, pos)

    def set_selection_pos(self, start_pos: str, end_pos: str) -> None:
        """Set selection position."""
        if self.widget is None:
            return
        try:
            text: tk.Text = self.widget
            text.tag_remove('sel', "1.0", "end")
            text.tag_add('sel', start_pos, end_pos)
        except Exception as _:
            self.set_cursor_pos(start_pos)

    def pos_to_index(self, pos: str) -> str:
        """Convert position to index."""
        row, col = pos.split(".")
        row, col = int(row), int(col)
        text = self.get_text()
        retcode = "\r\n" if "\r\n" in text else "\n"
        retcode_len = len(retcode)
        start = 0
        for i, line in enumerate(text.split("\n")):
            if (row - 1) == i:
                start += col
                break
            start += len(line) + retcode_len
        return start

    def index_to_pos(self, index: int) -> str:
        """Convert index to postion."""
        text = self.get_text()
        retcode = "\r\n" if "\r\n" in text else "\n"
        retcode_len = len(retcode)
        row = 1
        col = 0
        start = 0
        for line_no, line in enumerate(text.split("\n")):
            line_start = start
            line_end = line_start + len(line) + retcode_len
            start = line_end
            if index < line_end:
                row = line_no + 1
                col = index - line_start
                break
        return f"{row}.{col}"

    def get_cursor_pos(self) -> str:
        """Get Cursor position. liek `3.0` row=3, col=0"""
        if self.widget is None:
            return 0
        try:
            cur = self.widget.index("insert")
        except Exception as _:
            cur = ""
        return cur

    def set_cursor_pos(self, pos: str) -> None:
        """Set cursor position. (like `3.0`, row=3, col=0)"""
        if self.widget is None:
            return
        self.widget.mark_set(tk.INSERT, pos)

    def get_selection_start(self) -> int:
        """get selection start"""
        if self.widget is None:
            return 0
        try:
            sel_start, _ = self.widget.tag_ranges("sel")
            return self.pos_to_index(sel_start)
        except Exception as _:
            pos = self.get_cursor_pos()
            return self.pos_to_index(pos)
        
    def set_selection_start(self, index: int, sel_length: int=0) -> None:
        """set selection start"""
        pos1 = self.index_to_pos(index)
        pos2 = self.index_to_pos(index + sel_length)
        if sel_length > 0:
            self.set_selection_pos(pos1, pos2)
        else:
            self.set_cursor_pos(pos1)

    def get_selection_length(self) -> int:
        """get selection length"""
        if self.widget is None:
            return 0
        try:
            text = self.get_selected_text()
            return len(text)
        except Exception as _:
            return 0

    def select_all(self) -> None:
        """select all text"""
        if self.widget is None:
            return
        text: tk.Text = self.widget
        text.tag_add(tk.SEL, "1.0", tk.END)
        text.mark_set(tk.INSERT, '1.0')
        self.widget.see(tk.INSERT)

    def print(self, text: str, text_color: Union[str, None] = None, background_color: Union[str, None] = None, end:str="\n") -> None:
        """Print text."""
        text += end
        if self.widget is None:
            return
        tags: list[str] = []
        if text_color is not None:
            tag = generate_element_style_key("--multiline-text_color")
            self.widget.tag_config(tag, foreground=text_color)
            tags.append(tag)
        if background_color is not None:
            tag = generate_element_style_key("--multiline-background_color")
            self.widget.tag_config(tag, background=background_color)
            tags.append(tag)
        self.widget.insert("end", text, tags)
        if self.autoscroll:
            self.widget.see(tk.END)

class Textarea(Multiline):
    """Textarea element. (alias of Multiline)"""
    pass

class Output(Multiline):
    """Output element. (alias of Multiline) TODO: implement"""
    pass

class Slider(Element):
    """Slider element."""
    def __init__(
                self,
                range: tuple[float, float] = (1, 10), # value range (from, to)
                default_value: Union[float, None] = None, # default value
                resolution: Union[float, None] = None, # value resolution
                orientation: OrientationType = "horizontal", # orientation (h|v|horizontal|vertical)
                tick_interval: Union[float, None] = None, # tick marks interval on the scale
                enable_events: bool = False, # enable changing events
                enable_changed_events: bool = False, # enable changed event
                disable_number_display: bool = False, # hide number display
                size: Union[tuple[int, int], None] = None, # size (unit: character) / horizontal: (bar_length, thumb_size), vertical: (thumb_size, bar_length)
                key: Union[str, None] = None,
                # other
                default: Union[float, None] = None, # same as default_value
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        style_name = "Horizontal.TScale" if (orientation == "h" or orientation == "horizontal") else "Vertical.TScale"
        super().__init__("Slider", style_name, key, True, metadata, **kw)
        # common parameters
        self.has_value = True
        self.has_font_prop = False
        # range and resolution
        self.range = range
        self.resolution = resolution # dummy @see Slider.create
        if tick_interval is not None:
            self.props["tickinterval"] = tick_interval
        # set default_value or default
        self.default_value = default_value if default_value is not None else range[0]
        if default is not None:
            self.default_value = default
        # check orientation
        if orientation == "v":
            orientation = "vertical"
        elif orientation == "h":
            orientation = "horizontal"
        self.orientation: OrientationType = orientation
        self.props["orient"] = orientation
        # size
        self.slider_size = size
        # look
        if disable_number_display:
            self.props["showvalue"] = 0 # hide number
        # events
        self.enable_events = enable_events
        if enable_changed_events:
            self.bind_events({
                "<ButtonRelease-1>": "release"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create the widget."""
        # bar size
        if (self.slider_size is not None) and (len(self.slider_size) == 2):
            size = self.slider_size
            if self.orientation == "horizontal":
                length = size[0] * win.font_size_average[0]
                width = size[1] * win.font_size_average[1]
            else:
                width = size[0] * win.font_size_average[0]
                length = size[1] * win.font_size_average[1]
            self.props["width"] = width
            self.props["length"] = length
        # var
        self.scale_var = tk.DoubleVar()
        self.scale_var.set(self.default_value)
        # command
        command = None
        def on_command(*event):
            self.disptach_event({"event_type": "change", "event": event})
        if self.enable_events:
            command = on_command
        # widget
        self.widget = tk.Scale(
            parent,
            from_=self.range[0],
            to=self.range[1],
            resolution=self.resolution,
            command=command,
            variable=self.scale_var,
            **self.props)
        return self.widget

    def get(self) -> Any:
        """Return slider value."""
        return self.scale_var.get()
    
    def set(self, value: float) -> None:
        """Set value of Slider"""
        self.widget.set(value)
    
    def set_range(self, from_: float, to: float) -> None:
        """Set the range of the slider."""
        self.widget.config(from_=from_, to=to)

    def get_range(self) -> tuple[float, float]:
        return (self.widget.cget("from"), self.widget.cget("to"))

    def update(
        self,
        value: Union[float, None] = None,
        range: Union[tuple[float, float], None] = None,
        disable_number_display: Union[bool, None] = None,
        **kw,
    ) -> None:
        """Update the widget."""
        if range is not None:
            self.set_range(range[0], range[1])
        if disable_number_display is not None:
            self.props["showvalue"] = 0 if disable_number_display else 1
        if value is not None:
            self.set(value)
        else:
            self._widget_update(**kw)

class Canvas(Element):
    """
    Canvas element.
    This widget provides the same drawing methods as [tk.Canvas](https://tkdocs.com/tutorial/canvas.html).
    methods: create_line/create_rectangle/create_oval/create_polygon/create_arc/create_image/delete etc...
    """
    def __init__(
                self,
                key: Union[str, None] = None,
                enable_events: bool = False,
                background_color: Union[str, None] = None,
                size: tuple[int, int] = (300, 300),
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("Canvas", "", key, False, metadata, **kw)
        self.props["size"] = size
        self.has_font_prop = False
        if background_color:
            self.props["background"] = background_color
        if enable_events:
            self.bind_events({
                "<ButtonPress>": "mousedown",
                "<ButtonRelease>": "mouseup",
                "<Motion>": "mousemove"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.widget = tk.Canvas(parent, **self.props)
        return self.widget
    
    def clear(self) -> None:
        """Clear the canvas."""
        self.widget.delete("all")

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)
    
    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget", "tk_canvas", "TKCanvas"]: # compatibility with PySimpleGUI
            return self.widget
        return super().__getattr__(name)

class Graph(Element):
    """Graph element."""
    def __init__(
            self, key: Union[str, None] = None,
            background_color: Union[str, None] = None,
            size: tuple[int, int]=(300, 300),
            canvas_size: Union[tuple[int, int], None] = None,
            graph_bottom_left: Union[tuple[int, int], None] = None,
            graph_top_right: Union[tuple[int, int], None] = None,
            # other
            metadata: Union[dict[str, Any], None] = None,
            **kw) -> None:
        super().__init__("Graph", "", key, False, metadata, **kw)
        self.has_font_prop = False
        # <Coordinate> graph_Declared for compatibility, but not yet implemented.
        self.graph_bottom_left = graph_bottom_left
        self.graph_top_right = graph_top_right
        # </Coordinate>
        # <size>
        self.props["size"] = size
        if canvas_size is not None:
            self.props["size"] = canvas_size
        # </size>
        if background_color:
            self.props["background"] = background_color
        self.parent_window: Window|None = None

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.widget: tk.Canvas = tk.Canvas(parent, **self.props)
        self.parent_window = win
        return self.widget

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        self._widget_update(**kw)
    
    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget"]:
            return self.widget
        return super().__getattr__(name)
    
    def draw_line(self, point_from: PointType, point_to: PointType, color: str = 'black', width: int = 1) -> int:
        """Draw a line."""
        return self.widget.create_line(point_from, point_to, fill=color, width=width)
    
    def draw_lines(self, points: list[PointType], color='black', width=1) -> int:
        """Draw lines."""
        return self.widget.create_line(points, fill=color, width=width)
    
    def draw_point(self, point: PointType, size: int = 2, color: str = 'black') -> int:
        """Draw a point."""
        x, y = point
        size2: float = size / 2
        return self.widget.create_oval(x-size2, y-size2, x+size2, y+size2, fill=color)
    
    def draw_circle(self, center_location: PointType, radius: Union[int, float], fill_color: Union[str, None] = None, line_color: Union[str, None] = 'black', line_width: int = 1) -> int:
        """Draw a circle."""
        x, y = center_location
        return self.widget.create_oval(x-radius, y-radius, x+radius, y+radius, fill=fill_color, outline=line_color, width=line_width)

    def draw_oval(self, top_left: PointType, bottom_right: PointType, fill_color: Union[str, None] = None, line_color: Union[str, None] = None, line_width: int = 1):
        """Draw an oval."""
        return self.widget.create_oval(top_left, bottom_right, fill=fill_color, outline=line_color, width=line_width)
    
    def draw_arc(self, top_left: PointType, bottom_right: PointType, extent: Union[int, None] = None, start_angle: Union[int, None] = None, style: Union[str, None] = None, arc_color: Union[str, None] = 'black', line_width: int = 1, fill_color: Union[str, None] = None) -> int:
        """Draw an arc."""
        return self.widget.create_arc(top_left, bottom_right, extent=extent, start=start_angle, style=style, outline=arc_color, width=line_width, fill=fill_color)
    
    def erase(self) -> None:
        """Delete all"""
        self.widget.delete("all")
    
    def draw_rectangle(self, top_left: PointType, bottom_right: PointType, fill_color: Union[str, None] = None, line_color: Union[str, None] = None, line_width: Union[int, None] = None) -> int:
        """Draw rectangle"""
        return self.widget.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1], fill=fill_color, outline=line_color, width=line_width)
    
    def draw_polygon(self, points: list[PointType], fill_color: Union[str, None] = None, line_color: Union[str, None] = None, line_width: Union[int, None] = None) -> None:
        """Draw polygon"""
        return self.widget.create_polygon(points, fill=fill_color, outline=line_color, width=line_width)
    
    def draw_text(self, text: str, location: PointType, color: Union[str, None]='black', font: FontType = None, angle: Union[float, str, None] = 0, text_location: TextAlign = tk.CENTER) -> int:
        """Draw text"""
        x, y = location
        anchor = {"left": "w", "right": "e", "center": "center"}[text_location]
        return self.widget.create_text(x, y, text=text, font=font, fill=color, angle=angle, anchor=anchor)
    
    def draw_image(self, filename: Union[str, None] = None, data: Union[bytes, None] = None, location: Union[PointType, None] = None) -> int:
        """Draw image"""
        # check location
        if location is None:
            location = (0, 0)
        # load image
        image: tk.PhotoImage|None = get_image_tk(filename=filename, data=data)
        # important
        self.widget.image = image # type: ignore
        return self.widget.create_image(location, image=image, anchor=tk.NW)

class Image(Element):
    """Image element."""
    def __init__(
                self,
                source: Union[bytes, str, None] = None, # image source
                filename = None, # filen ame
                data: bytes = None, # image data
                key: Union[str, None] = None,
                background_color: Union[str, None] = None,
                size: tuple[int, int] = (300, 300),
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("Image", "", key, False, metadata, **kw)
        self.has_font_prop = False
        self.source = source
        self.filename = filename
        self.data = data
        self.size = self.props["size"] = size
        if background_color is not None:
            self.props["background"] = background_color

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Image widget."""
        self.widget = tk.Canvas(parent, **self.props)
        try:
            self.set_image(self.source, self.filename, self.data)
        except Exception:
            pass
        return self.widget

    def get(self) -> Any:
        """Return Widget"""
        return self.widget

    def erase(self) -> None:
        """Erase image"""
        self.widget.delete("all")

    def set_image(self,
            source: Union[bytes, str, None] = None,
            filename: Union[str, None] = None,
            data: Union[bytes, None]=None) -> None:
        if self.widget is None:
            return
        # set 
        self.filename = filename
        self.data = data
        # erase
        self.erase()
        # load
        photo = get_image_tk(source, filename, data, self.size)
        if photo is not None:
            self.widget.create_image(0, 0, image=photo, anchor="nw")
            self.widget.photo = photo # type ignore

    def update(self,
               source: Union[bytes, str, None] = None,
               filename: Union[str, None] = None,
               data: Union[bytes, None] = None,
               size: Union[tuple[int,int], None] = None,
               **kw) -> None:
        """Update the widget."""
        if size is not None:
            self.size = size
            self.widget.configure(width=size[0], height=size[1])
        if (source is not None) or (filename is not None) or (data is not None):
            self.set_image(source, filename, data)
        self._widget_update(**kw)
    
    def __getattr__(self, name):
        """Get unknown attribute."""
        if name in ["Widget", "tk_canvas", "tktext_label"]:
            return self.widget
        return super().__getattr__(name)

class VSeparator(Element):
    """VSeparator element."""
    def __init__(
                self,
                key: Union[str, None] = None,
                background_color: Union[str, None] = None,
                pad: PadType = 5,
                size: tuple[int, int]=(5, 100),
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("VSeparator", "TSeparator", key, False, metadata, **kw)
        self.use_ttk = True
        size = (pad, size[1])
        self.size = self.props["size"] = size
        self.props["padx"] = pad
        if background_color is not None:
            self.props["background"] = background_color
        self.props["expand_y"] = True
    
    def create(self, win: Window, parent: tk.Widget) -> Any:
        self.widget = ttk.Separator(parent, orient="vertical")
        return self.widget

class HSeparator(Element):
    """HSeparator element."""
    def __init__(
                self,
                key: Union[str, None] = None,
                background_color: Union[str, None] = None,
                pad: PadType = 5,
                size: tuple[int, int] = (100, 5),
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("HSeparator", "TSeparator", key, False, metadata, **kw)
        self.use_ttk = True
        size = (size[1], pad)
        self.size = self.props["size"] = size
        self.props["pady"] = pad
        if background_color is not None:
            self.props["background"] = background_color
        self.props["expand_x"] = True
    
    def create(self, win: Window, parent: tk.Widget) -> Any:
        self.widget = ttk.Separator(parent, orient="horizontal")
        return self.widget


class Listbox(Element):
    """Listbox element."""
    def __init__(
        self,
        values: list[str] = [],
        default_values: Union[list[str], None] = None,  # selected values
        default_value: Union[str, None] = None,  # a default value
        key: Union[str, None] = None,
        enable_events: bool = False,
        select_mode: ListboxSelectMode = LISTBOX_SELECT_MODE_BROWSE,
        # other
        metadata: Union[dict[str, Any], None] = None,
        items: Union[list[str], None] = None,  # same as values (alias values)
        **kw,
    ) -> None:
        super().__init__("Listbox", "", key, True, metadata, **kw)
        self.values = values
        if items is not None: # alias
            self.values = items
        self.select_mode = select_mode
        if default_value is not None:
            default_values = [default_value]
        self.default_values = default_values
        # event
        if enable_events:
            self.bind_events({
                "<<ListboxSelect>>": "select"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """[Listbox.create] create Listbox widget"""
        self.window: Window = win
        # create frame
        self.widget_frame: tk.Frame = tk.Frame(parent)
        # create listbox and scrollbar
        self.widget:tk.Listbox = tk.Listbox(self.widget_frame, selectmode=self.select_mode, **self.props)
        self.widget_scrollbar = tk.Scrollbar(self.widget_frame,command=self.widget.yview)
        self.widget.config(yscrollcommand=self.widget_scrollbar.set)
        # pack
        self.widget.pack(side="left", fill="both", expand=True)
        self.widget_scrollbar.pack(side="right", fill="y")
        # insert values
        self.set_values(self.values)
        self.select_values(self.default_values)
        return self.widget_frame

    def select_values(self, values: tuple[list[str], None]) -> None:
        """Select values"""
        if self.widget is None:
            return
        if values is None:
            return
        for v in values:
            try:
                index = self.values.index(v)
                self.widget.selection_set(index)
            except ValueError:
                pass

    def set_values(self, values: list[str]) -> None:
        """Set values to list"""
        self.values = values
        if self.widget is not None:
            # delete all
            self.widget.delete(0, "end")
            # insert data
            for i, v in enumerate(self.values):
                self.widget.insert(i, v)

    def get_cursor_index(self) -> int:
        """Get cursor index (return -1 if not selected)"""
        if self.widget is None:
            return None
        wg: tk.Listbox = self.widget
        selections = wg.curselection()
        if selections is None or len(selections) == 0:
            return -1
        return selections[0]
    
    def set_cursor_index(self, index: int) -> None:
        """Set cursor index"""
        if self.widget is None:
            return
        try:
            self.widget.select_clear(0, "end")
            self.widget.selection_set(index)
            self.widget.see(index)
        except Exception as _:
            pass

    def get(self) -> Any:
        """Get the value of the widget."""
        if self.widget is None:
            return None
        wg: tk.Listbox = self.widget
        selected: list[str] = []
        selections: Any = wg.curselection()
        if selections is not None:
            for i in selections:
                index: int = int(i)
                selected.append(self.values[index])
        return selected

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        if self.widget is None:
            return
        if len(args) >= 1:
            values = args[0]
            self.set_values(values)
        if "values" in kw:
            self.set_values(kw.pop("values"))
        self._widget_update(**kw)

class Combo(Element):
    """Combo element."""
    def __init__(
                self,
                values: list[str]=[],
                default_value: str="",
                key: Union[str, None] = None,
                enable_events: bool = False,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        super().__init__("Combo", "TCombobox", key, True, metadata, **kw)
        self.values = values
        self.value: tk.StringVar|None = None
        self.default_value = default_value
        # event
        if enable_events:
            self.bind_events({
                "<<ComboboxSelected>>": "select"
            }, "system")

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """[Combo.create] create Listbox widget"""
        self.value = tk.StringVar()
        self.widget = ttk.Combobox(parent, values=self.values, textvariable=self.value, **self.props)
        self.set_value(self.default_value)
        return self.widget

    def set_values(self, values: list[str]) -> None:
        """Set values to list"""
        self.values = values
        if self.widget is not None:
            self._widget_update(values=self.values)
    
    def set_value(self, v: str) -> None:
        """Set the value of the widget."""
        self.value.set(v)

    def get(self) -> Any:
        """Get the value of the widget."""
        if self.widget is None:
            return None
        return self.value.get()

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        if self.widget is None:
            return
        if len(args) >= 1:
            self.set_value(args[0])
        if "values" in kw:
            self.set_values(kw.pop("values"))
        if "value" in kw:
            self.set_value(kw.pop("value"))
        self._widget_update(**kw)

class Table(Element):
    """Table element."""
    def __init__(
                self,
                values: list[list[str]] = [], # Specify the table values as 2D list.
                headings: list[str] = [], # Specify the table header as a list.
                key: Union[str, None] = None,
                justification: TextAlign = "center",
                auto_size_columns: bool = True,
                max_col_width: int = 0,
                col_widths: Union[list[int], None] = None,
                enable_events: bool = False,
                event_returns_values: Union[bool, None] = None, # Returns the table value if set to True, otherwise returns the index.
                select_mode: str="browse",
                max_columns: int = 20, # This property cannot be changed later. It is advisable to set a larger value.
                vertical_scroll_only: bool = True, # vertical scroll only
                # text props
                text_align: Union[TextAlign, None] = "left", # text align
                font: Union[FontType, None] = None, # font
                color: Union[str, None] = None, # text color
                text_color: Union[str, None] = None, # same as color
                background_color: Union[str, None] = None, # background color
                # pack props
                expand_x: bool = False,
                expand_y: bool = False,
                pad: Union[PadType, None] = None,
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw) -> None:
        """Create a table."""
        # super().__init__("Table", "Treeview", key, metadata, **kw)
        super().__init__("Table", "", key, True, metadata, **kw)
        self.ttk = True
        self.values = values
        self.headings = headings
        self.enable_events = enable_events
        self.select_mode = select_mode
        self.auto_size_columns = auto_size_columns
        self.max_col_width = max_col_width
        self.col_widths = col_widths
        self.has_font_prop = False # has, but not widget root
        self.vertical_scroll_only = vertical_scroll_only
        # check headings
        if len(self.headings) < max_columns:
            for i in range(max_columns - len(self.headings)):
                self.headings.append("") # add dummy
        # event_returns_values ?
        self.event_returns_values: bool = not _compatibility
        if event_returns_values is not None:
            self.event_returns_values = event_returns_values 
        # justification
        if justification is not None:
            self.justification: str = self._justify_to_anchor(justification)
        if text_align is not None:
            self.justification: str = self._justify_to_anchor(justification)
        # set props
        self._set_text_props(font=font, color=color, text_color=text_color, background_color=background_color)
        self._set_pack_props(expand_x=expand_x, expand_y=expand_y, pad=pad)
        # check col_widths
        if self.col_widths is None:
            self.col_widths = [len(s) for s in self.headings]
            for row in self.values:
                for i, cell in enumerate(row):
                    v = max(self.col_widths[i], len(str(cell))+1)
                    if (self.max_col_width is not None) and (self.max_col_width > 0):
                        v = min(v, self.max_col_width)
                    self.col_widths[i] = v
    
    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        """Create a Table widget."""
        self.window: Window = win
        # create treeview
        # - FRAME
        self.frame = ttk.Frame(parent, padding=1, relief="ridge", borderwidth=1)
        columns = tuple(i+1 for i, _ in enumerate(self.headings))
        # - TREE (font)
        font = None
        if "font" in self.props:
            font = self.props.pop("font")
        # - TREE
        tree = self.widget = ttk.Treeview(
            self.frame,
            columns=columns,
            show="headings",
            **self.props)
        self.props["font"] = font
        # - SCROLLBAR
        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        if not self.vertical_scroll_only:
            hscrollbar = ttk.Scrollbar(self.frame, orient="horizontal", command=tree.xview)
            tree.configure(xscroll=hscrollbar.set)
        # - pack to frame
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        if not self.vertical_scroll_only:
            hscrollbar.grid(row=1, column=0, sticky="ew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # setting for column
        streatch = tk.YES if self.auto_size_columns else tk.NO
        for i, h in enumerate(self.headings):
            self.widget.heading(i+1, text=h, anchor="center")
            kw: dict[str, Any] = {"stretch": streatch}
            if self.justification != "":
                kw["anchor"] = self.justification
            if self.col_widths is not None:
                # get font size
                font_w = 12
                if (self.font is not None) and (len(self.font) >= 2):
                    font_w = self.font[1]
                if h == "":
                    kw["width"] = 0 # hidden column
                else:
                    kw["width"] = self.col_widths[i % len(self.col_widths)] * font_w
            self.widget.column(i+1, **kw)
        # add data
        self.set_values(self.values, self.headings)
        if self.enable_events:
            self.widget.bind("<<TreeviewSelect>>", lambda e: self._table_events(e))
        return self.frame
    
    def set_values(self, values: list[list[str]], headings: Union[list[str], None] = None) -> None:
        """Set values to the table."""
        if self.widget is None:
            return
        self.values = values
        if headings is not None:
            self.headings = headings
        # clear
        for row in self.widget.get_children():
            self.widget.delete(row)
        # update heading
        if headings is not None:
            for i, h in enumerate(self.headings):
                self.widget.heading(i+1, text=h, anchor="center")
                if h == "":
                    self.widget.column(i+1, width=0, stretch=tk.NO)
        # add data
        for row_no, row in enumerate(self.values):
            self.widget.insert(parent="", iid=row_no, index="end", values=row)
    
    def get(self) -> Any:
        """Get the value of the widget."""
        if self.widget is None:
            return []
        record_ids = self.widget.focus()
        if self.event_returns_values:
            record_values = self.widget.item(record_ids, "values")
        else:
            if record_ids is None or record_ids == "":
                record_values = []
            else:
                if isinstance(record_ids, str):
                    record_ids = [record_ids]
                record_values = list(map(lambda id_s: int(id_s), record_ids))
        return record_values

    def _table_events(self, _event: Any) -> None:
        """Handle events."""
        self.window._event_handler(self.key, {})

    def update(self, *args, **kw) -> None:
        """Update the widget."""
        if len(args) >= 1:
            values = args[0]
            kw["values"] = values
        if "max_columns" in kw:
            raise TkEasyError("Table.max_columns cannot be changed; it can only be set in the constructor.")
        if "headings" in kw:
            new_heading = kw["headings"]
            del kw["headings"]
            # ヘッダ更新処理 #54
            # 旧ヘッダを処理
            for i, _h in enumerate(self.headings):
                h2 = new_heading[i] if len(new_heading) > i else ""
                self.widget.heading(i+1, text=h2, anchor="center")
                if h2 == "":
                    self.widget.column(i+1, width=0)
            # 新ヘッダを処理
            for i, h in enumerate(new_heading):
                self.widget.heading(i+1, text=h, anchor="center")
                self.widget.column(i+1, width=100, stretch=tk.YES)
            self.headings = new_heading

        if "values" in kw:
            self.values = kw["values"]
            # update list
            if self.widget is not None:
                tree = self.widget
                for i in tree.get_children(): # clear all
                    tree.delete(i)
            # set values
            self.set_values(self.values)
            del kw["values"]
        # update
        self._widget_update(**kw)

#------------------------------------------------------------------------------
# Browse elements

class FileBrowse(Element):
    """
    FileBrowse element.
    """
    def __init__(
                self, button_text: str="...",
                key: Union[str, None] = None,
                title: str = "",
                target_key: Union[str, None] = None,
                file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
                multiple_files: bool = False,
                initial_folder: Union[str, None] = None,
                save_as: bool = False,
                enable_events: bool = False, # enable changing events
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        if key is None or key == "":
            key = generate_element_style_key("Browse")
        super().__init__("FileBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.file_types = file_types
        self.save_as = save_as
        self.multiple_files = multiple_files
        self.initial_folder = initial_folder
        self.props["text"] = button_text
        self.enable_events = enable_events

    def create(self, win: Window, parent: tk.Widget) -> tk.Widget:
        self.widget = tk.Button(parent, **self.props)
        # hook
        event_name = "--browse_action/hide"
        self.bind_events({
            "<Button-1>": event_name,
            "<Return>": event_name,
        })
        win.register_event_hooks({
            f"{self.key}{event_name}": [self.show_dialog]
        })
        return self.widget
    
    def _get_initial_directory(self) -> str:
        target: tk.Widget = self.get_prev_widget(self.target_key)
        # get initial directory
        init_dir = self.initial_folder
        if target is not None:
            try:
                target_text = str(target.get())
            except Exception:
                target_text = ""
            if target_text != "":
                init_dir = os.path.dirname(target_text)
        return init_dir

    def show_dialog(self, *args) -> Union[str, None]:
        """Show file dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        # get initial directory
        init_dir = self._get_initial_directory()
        # popup
        result = dialogs.popup_get_file(
            title=self.title,
            initial_folder=init_dir,
            save_as=self.save_as,
            file_types=self.file_types,
            multiple_files=self.multiple_files,
        )
        if isinstance(result, list) or isinstance(result, tuple):
            result = ";".join(result)
        if (target is not None) and (result is not None) and (result != ""):
            target.update(result)
            if self.enable_events:
                self.window._event_handler(self.key, {"event": result, "event_type": "change"})
        return result
    
    def set_text(self, text: str) -> None:
        """Set the text of the button."""
        self.props["text"] = text
        self._widget_update(text=text)

    def update(self, text: Union[str, None] = None, **kw) -> None:
        """Update the widget."""
        if text is not None:
            self.set_text(text)
        self._widget_update(**kw)

class FilesBrowse(FileBrowse):
    """FilesBrowse element."""
    def __init__(
                self,
                button_text: str = "...",
                key: Union[str, None] = None,
                target_key: Union[str, None] = None,
                title: str="",
                file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
                enable_events: bool = False, # enable changing events
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        super().__init__("FilesBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.file_types = file_types
        self.props["text"] = button_text
        self.enable_events = enable_events
        # force set params
        self.multiple_files = True
        self.save_as = False

class FileSaveAsBrowse(FileBrowse):
    """FileSaveAsBrowse element."""
    def __init__(
                self,
                button_text: str="...",
                key: Union[str, None] = None,
                target_key: Union[str, None] = None,
                title: str = "",
                file_types: tuple[tuple[str, str]] = (("All Files", "*.*"),),
                enable_events: bool = False, # enable changing events
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        super().__init__("FileSaveAsBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.file_types = file_types
        self.props["text"] = button_text
        self.enable_events = enable_events
        # force set params
        self.multiple_files = False
        self.save_as = True

class FileSaveAs(FileSaveAsBrowse):
    """FileSaveAs element. (alias of FileSaveAsBrowse)"""
    pass

class FolderBrowse(FileBrowse):
    """FolderBrowse element."""
    def __init__(
                self,
                button_text: str="...",
                key: Union[str, None] = None,
                target_key: Union[str, None] = None,
                default_path: Union[str, None] = None,
                title: str = "",
                enable_events: bool = False, # enable changing events
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        super().__init__("FolderBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.default_path = default_path
        self.props["text"] = button_text
        self.enable_events = enable_events
    
    def show_dialog(self, *args) -> Union[str, None]:
        """Show file dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        # popup
        result = dialogs.popup_get_folder(
            title=self.title,
            default_path=self.default_path,
        )
        if (target is not None) and (result is not None) and (result != ""):
            target.update(result)
            if self.enable_events:
                self.window._event_handler(self.key, {"event": result, "event_type": "change"})
        return result

class ColorBrowse(FileBrowse):
    """FolderBrowse element."""
    def __init__(
                self,
                button_text: str="...",
                key: Union[str, None] = None,
                target_key: Union[str, None] = None,
                default_color: Union[str, None] = None,
                title: str="",
                enable_events: bool = False, # enable changing events
                # other
                metadata: Union[dict[str, Any], None] = None,
                **kw
                ) -> None:
        super().__init__("FolderBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.default_color = default_color
        self.props["text"] = button_text
        self.enable_events = enable_events
    
    def show_dialog(self, *args) -> Union[str, None]:
        """Show file dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        # popup
        result = dialogs.popup_color(
            title=self.title,
            default_color=self.default_color,
        )
        if (target is not None) and (result is not None) and (result != ""):
            target.update(result)
            if self.enable_events:
                self.window._event_handler(self.key, {"event": result, "event_type": "change"})
        return result

class ListBrowse(FileBrowse):
    """ListBrowse element."""

    def __init__(
        self,
        values: list[str] = [],
        message: str = "",
        button_text: str = "...",
        default_value: Union[str, None] = None,  # default value
        key: Union[str, None] = None,
        target_key: Union[str, None] = None,
        title: str = "",
        font: Union[FontType, None] = None,
        enable_events: bool = False,  # enable changing events
        # other
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("ListBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.props["text"] = button_text
        self.enable_events = enable_events
        self.values = values
        self.message = message
        self.font = font
        self.default_value = default_value

    def show_dialog(self, *args) -> Union[str, None]:
        """Show Listbox dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        if target is not None:
            val = target.get()
            if (val != "") and (val in self.values):
                self.default_value = val
        # popup
        result = dialogs.popup_listbox(
            values=self.values,
            default_value=self.default_value,
            message=self.message,
            title=self.title,
            font=self.font,
        )
        if (target is not None) and (result is not None) and (result != ""):
            target.update(result)
            if self.enable_events:
                self.window._event_handler(self.key, {"event": result, "event_type": "change"})
        return result

class MultilineBrowse(FileBrowse):
    """MultilineBrowse element."""

    def __init__(
        self,
        message: str = "",
        key: Union[str, None] = None,
        button_text: str = "...",
        target_key: Union[str, None] = None,
        title: str = "",
        font: Union[FontType, None] = None,
        enable_events: bool = False,  # enable changing events
        # other
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("ListBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.props["text"] = button_text
        self.enable_events = enable_events
        self.message = message
        self.font = font

    def show_dialog(self, *args) -> Union[str, None]:
        """Show Listbox dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        if target is not None:
            val = target.get()
            if (val != ""):
                val = val.replace("\\n", "\n")
                self.message = val
        # popup
        result = dialogs.popup_scrolled(
            message=self.message,
            title=self.title,
            font=self.font,
        )
        if (target is not None) and (result is not None) and (result != ""):
            result = result.replace("\r", "")
            result = result.replace("\n", "\\n")
            target.update(result)
            if self.enable_events:
                self.window._event_handler(
                    self.key, {"event": result, "event_type": "change"}
                )
        return result


class CalendarBrowse(FileBrowse):
    """CalendarBrowse element."""

    def __init__(
        self,
        button_text: str = "...",
        key: Union[str, None] = None,
        target_key: Union[str, None] = None,
        default_date: Union[datetime, None] = None,
        date_format: Union[str, None] = "%Y-%m-%d",
        title: str = "",
        enable_events: bool = False,  # enable changing events
        # other
        metadata: Union[dict[str, Any], None] = None,
        **kw,
    ) -> None:
        super().__init__("CalendarBrowse", "", key, False, metadata, **kw)
        self.target_key = target_key
        self.title = title
        self.default_date = default_date
        self.props["text"] = button_text
        self.date_format = date_format
        self.enable_events = enable_events

    def show_dialog(self, *args) -> Union[str, None]:
        """Show file dialog"""
        target: tk.Widget = self.get_prev_widget(self.target_key)
        # popup
        result = dialogs.popup_get_date(
            title=self.title,
            current_date=self.default_date,
        )
        if (target is not None) and (result is not None) and (result != ""):
            target.update(result.strftime(self.date_format))
            if self.enable_events:
                self.window._event_handler(
                    self.key, {"event": result, "event_type": "change"}
                )
        return result

class CalendarButton(CalendarBrowse):
    """CalendarButton element. (alias of CalendarBrowse)"""
    pass


def rgb(r: int, g: int, b: int) -> str:
    """Convert RGB to Hex"""
    r = r & 0xFF
    g = g & 0xFF
    b = b & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"

def image_resize(img: PILImage, size: tuple[int, int]) -> PILImage:
    """Resize image"""
    if size[0] < size[1]:
        r = size[0] / img.size[0]
    else:
        r = size[1] / img.size[1]
    w, h = size[0], int(img.size[1] * r)
    return img.resize(size=(w, h))

def get_image_tk(
        source: Union[bytes, Union[str, None]] = None,
        filename: Union[str, None] = None,
        data: Union[bytes, None] = None,
        size: Union[tuple[int, int], None] = None) -> Union[tk.PhotoImage, None]:
    """Get Image for tk"""
    # if source is bytes, set data
    if source is not None:
        if isinstance(source, str): # is filename
            filename = source
        else: # is data
            data = source
    # load from file?
    if filename is not None:
        try:
            img: PILImage = PILImage.open(filename)
            if size is not None:
                img = image_resize(img, size)
            return ImageTk.PhotoImage(image=img)
        except Exception as e:
            raise TkEasyError(f"TkEasyGUI.Image.set_image.Error: filename='{filename}', {e}")
    # load from data
    if data is not None:
        try:
            # check if data is PILImage
            if isinstance(data, PILImage.Image):
                img: PILImage = data
                if size is not None:
                    img = image_resize(img, size)
                return ImageTk.PhotoImage(image=img)
            return ImageTk.PhotoImage(data=data)
        except Exception as e:
            print("[TkEasyGUI] get_image_tk.Error:", e, stderr=True)
            return data
    return None

def imagedata_to_bytes(image_data: PILImage) -> bytes:
    """Convert JPEG to PNG"""
    img_bytes = io.BytesIO()
    image_data.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    return img_bytes

def imagefile_to_bytes(filename: str) -> bytes:
    """Read image file and convert to bytes"""
    image = PILImage.open(filename)
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    return img_bytes

def time_checker_start() -> datetime:
    """timer start"""
    return datetime.now()

def time_checker_end(start_time: datetime) -> int:
    """timer end"""
    elapsed_time = (datetime.now() - start_time).total_seconds()
    msec = int(elapsed_time * 1000)
    return msec

# get system info

def get_tk_version() -> str:
    """Get tk version"""
    root = get_root_window()
    tkversion = root.tk.call("info", "patchlevel")
    return tkversion

def get_tcl_version() -> str:
    """Get tcl version"""
    root = get_root_window()
    tclversion = root.tk.call("info", "tclversion")
    return tclversion

def get_font_list() -> list[str]:
    """Get font list"""
    root = get_root_window()
    root.withdraw()
    return list(tkfont.families())

def get_system_info():
    # node={platform.node()}
    py_ver = sys.version.replace('\n', '')
    return f"""
tkeasygui={version.__version__}
python={py_ver}
tcl_tk={get_tk_version()}
os={platform.system()}
os_version={platform.version()}
os_release={platform.release()}
architecture={platform.architecture()}
processor={platform.processor()}
    """.strip()


_compatibility = utils._compatibility
