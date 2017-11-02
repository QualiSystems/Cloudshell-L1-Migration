#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Tkinter import *


class Memory:

    def __init__(self):
        self.path = "runtime_data.json"
        self.data = {}

    def set(self, key, value):
        self.data[key] = value
        self.save()
        return

    def get(self, key):
        return self.data.get(key)

    def restore(self):
        return json.loads(open(self.path, 'r').read())

    def save(self):
        f = open(self.path, 'w')
        f.write(json.dumps(self.data))
        f.close()
        return

    def clear(self):
        f = open(self.path, 'w')
        f.close()

memory = Memory()


class OhadTkinterObject:

    def __init__(self, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs['id']


class Screen(OhadTkinterObject):

    def __init__(self, window):
        OhadTkinterObject.__init__(self)
        self.window = window

    def run(self):
        self.window.mainloop()


class CustomWidget(OhadTkinterObject):

    def __init__(self, window, row, col, **kwargs):
        OhadTkinterObject.__init__(self, **kwargs)
        self.window = window
        self.row = row
        self.col = col
        self.last_row = -1
        self.last_column = -1

    def place(self):
        self.place_on_grid()
        self.get_dimensions()

    def place_on_grid(self):
        pass

    def get_dimensions(self):
        highest_row = 0
        highest_col = 0
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, Widget):
                widget_row = int(attr.grid_info()['row'])
                if widget_row > highest_row:
                    highest_row = widget_row
                widget_col = int(attr.grid_info()['column'])
                if widget_col > highest_col:
                    highest_col = widget_col
        self.last_row = highest_row
        self.last_column = highest_col


class OpenWindowButton(CustomWidget):

    def __init__(self, window, row, col, text, screen_object, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)
        self.screen = screen_object
        self.button = Button(self.window, text=text, command=self.show_screen_callback)

    def place_on_grid(self):
        self.button.grid(row=self.row, column=self.col)

    def show_screen_callback(self):
        screen = self.screen(Toplevel(self.window))
        screen.run()


class FilteringList(CustomWidget):

    def __init__(self, window, label, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)

        self.items = kwargs['items']
        self.list_label = Label(self.window, text=label)

        # Filter by name box
        self.search_var = StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.update_list())
        self.entry = Entry(self.window, textvariable=self.search_var)

        # Listbox
        self.items_listbox = Listbox(self.window)
        self.update_list()

    def place_on_grid(self):
        self.list_label.grid(row=self.row, column=self.col)
        self.entry.grid(row=self.row + 1, column=self.col)
        self.items_listbox.grid(row=self.row + 2, column=self.col)

    def update_list(self):
        search_term = self.search_var.get().encode('utf-8')

        # Just a generic list to populate the listbox
        items_listbox = self.items
        self.items_listbox.delete(0, END)

        for item in items_listbox:
            if search_term.lower() in item.lower():
                self.items_listbox.insert(END, item)


class DropDownList(CustomWidget):

    def __init__(self, window, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)

        # Create a Tkinter variable
        self.tkvar = StringVar(self.window)
        self.items = kwargs['items'] if 'items' in kwargs else []
        self.type = 'list' if 'items' in kwargs else 'bool'

        # Dictionary with options
        if self.type is 'list':
            choices = sorted(self.items, key=lambda x: x[1])
        else:
            choices = [True, False]

        if memory.get(self.id) is not None:
            current_choice = memory.get(self.id)
        else:
            try:
                current_choice = kwargs['default']
            except KeyError:
                current_choice = choices[0]
        self.tkvar.set(current_choice)  # set the default option
        self.popupMenu = OptionMenu(self.window, self.tkvar, *choices)
        # link function to change dropdown
        self.tkvar.trace('w', self.change_dropdown)

    def place_on_grid(self):
        self.popupMenu.grid(row=self.row, column=self.col)

    def change_dropdown(self, *args):
        choice = self.tkvar.get()
        memory.set(self.id, choice)

    def get_value(self):
        return self.tkvar.get()


class DynamicInputField(CustomWidget):

    def __init__(self, window, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)

        self.type = kwargs['type'] if 'type' in kwargs else 'str'
        self.label_text = kwargs['label'] if 'label' in kwargs else 'untitled'
        self.value = kwargs['value'] if 'value' in kwargs else ''

        self.label = Label(self.window, text=self.label_text)
        if self.type == 'str':
            self.input_field = Entry(self.window, width=50, text=self.value)
        elif self.type == 'list':
            self.items = kwargs['items'] if 'items' in kwargs else []
            self.input_field = DropDownList(self.window, self.row, self.col + 1, text=self.value, items=self.items, id=self.id)
        elif self.type == 'bool':
            self.default = kwargs['default'] if 'default' in kwargs else True
            self.input_field = DropDownList(self.window, self.row, self.col + 1, text=self.value, id=self.id, default=self.default)

    def place_on_grid(self):
        self.label.grid(row=self.row, column=self.col)
        if isinstance(self.input_field, CustomWidget):
            self.input_field.place_on_grid()
        else:
            self.input_field.grid(row=self.row, column=self.col + 1)


class ConfigMenu(CustomWidget):

    def __init__(self, window, row, col, fields_dict, **kwargs):
        CustomWidget.__init__(window, row, col, fields_dict, **kwargs)


if __name__ == '__main__':
    pass
