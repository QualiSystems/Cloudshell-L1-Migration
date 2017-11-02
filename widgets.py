#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import bs4
from Tkinter import *
from cloudshell.api.cloudshell_api import CloudShellAPISession


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


class DropDownList(CustomWidget):

    def __init__(self, window, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)

        # Create a Tkinter variable
        self.tkvar = StringVar(self.window)
        self.items = kwargs['items'] if 'items' in kwargs else []
        self.type = 'list' if 'items' in kwargs else 'bool'

        self.form = kwargs['form'] if 'form' in kwargs else None
        self.variable = kwargs['variable'] if 'variable' in kwargs else None

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

    def destroy(self):
        self.popupMenu.destroy()


class DynamicInputField(CustomWidget):

    def __init__(self, window, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)

        self.type = kwargs['type'] if 'type' in kwargs else 'str'
        self.label_text = kwargs['label'] if 'label' in kwargs else 'untitled'
        self.value = kwargs['value'] if 'value' in kwargs else ''

        self.label = Label(self.window, text=self.label_text)
        if self.type == 'str':
            self.input_field = Entry(self.window, width=15)
            self.input_field.insert(0, self.value)
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

    def get_value(self):
        for attr in dir(self):
            if isinstance(getattr(self, attr), Entry):
                entry = getattr(self, attr)
                return entry.get()


class Form(CustomWidget):
    """
    Form should get a dict object, where each key is a field, and the value is a dict 2 keys: value and rank (the rank is intended to order the fields in the gui, 0 on top)
    """

    def __init__(self, window, row, col, form_json_path, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)
        self.json_path = form_json_path
        self.dict = self.restore()

        for idx, key in enumerate(sorted(self.dict, key=lambda x: self.dict[x]['rank'])):
            setattr(self, key, DynamicInputField(self.window, self.row + idx, self.col, label=key, value=self.dict[key]['value']))
            getattr(self, key).place_on_grid()

        save_button = Button(self.window, text="Save", command=self.save)
        save_button.grid(row=self.row + len(self.dict) + 1, column=1)

    def save(self):
        for attr in dir(self):
            if isinstance(getattr(self, attr), DynamicInputField):
                field = getattr(self, attr)
                self.dict[attr]['value'] = field.get_value()
        f = open(self.json_path, 'w')
        f.write(json.dumps(self.dict))
        print "Form {} was saved successfully.".format(self.json_path)

    def restore(self):
        return json.loads(open(self.json_path, 'r').read())


class ResourcesForm(CustomWidget):

    def __init__(self, window, row, col, **kwargs):

        CustomWidget.__init__(self, window, row, col, **kwargs)
        self.families = self.get_families()

        self.family_names = list(set([x['family'] for x in self.families]))
        self.families_dropdown_label = Label(self.window, text='Resource Family')
        self.families_dropdown_label.grid(row=self.row, column=self.col)
        self.families_dropdown = DropDownList(self.window, self.row, self.col + 1, id='families_dropdown', items=self.family_names)
        self.families_dropdown.place_on_grid()
        self.set_family_button = Button(self.window, text='Set', command=self.set_family)
        self.set_family_button.grid(row=self.row, column=self.col + 2)

        self.model_names = []
        self.models_dropdown_label = Label(self.window, text='Resource Model')
        self.models_dropdown_label.grid(row=self.row + 1, column=self.col)
        self.models_dropdown = None
        self.set_model_button = Button(self.window, text='Set', command=self.set_model)

        self.dirver_names = []
        self.drivers_dropdown_label = Label(self.window, text='Resource Driver')
        self.drivers_dropdown_label.grid(row=self.row + 2, column=self.col)
        self.drivers_dropdown = None

    def set_family(self):
        try:
            self.models_dropdown.destroy()
        except AttributeError:
            pass
        self.model_names = list(set([x['model'] for x in self.families if x['family'] == self.families_dropdown.get_value()]))
        self.models_dropdown = DropDownList(self.window, self.row + 1, self.col + 1, id='models_dropdown', items=self.model_names)
        self.models_dropdown.place_on_grid()
        self.set_model_button.grid(row=self.row + 1, column=self.col + 2)

    def set_model(self):
        try:
            self.drivers_dropdown.destroy()
        except AttributeError:
            pass
        self.driver_names = list(set([x['driver'] for x in self.families if x['family'] == self.families_dropdown.get_value() and x['model'] == self.models_dropdown.get_value()]))
        self.drivers_dropdown = DropDownList(self.window, self.row + 2, self.col + 1, id='drivers_dropdown', items=self.driver_names)
        self.drivers_dropdown.place_on_grid()

    @staticmethod
    def get_families():
        credentials = json.loads(open("forms/credentials.json").read())
        api = CloudShellAPISession(credentials['host']['value'], credentials['username']['value'],
                                   credentials['password']['value'],
                                   credentials['domain']['value'])
        tree = api.ExportFamiliesAndModels().Configuration
        soup = bs4.BeautifulSoup(tree, 'xml')
        resource_families = []
        families = [x['Name'] for x in soup.find_all('ResourceFamily')]
        for family in families:
            family_models = [x['Name'] for x in soup.find('ResourceFamily', {'Name': family}).find_all('ResourceModel')]
            for model in family_models:
                drivers = [x.text for x in soup.find('ResourceModel', {'Name': model}).find_all('DriverName')]
                for driver in drivers:
                    resource_families.append({'family': family, 'model': model, 'driver': driver})
                    # print {'family': family, 'model': model, 'driver': driver}
        return resource_families


class ResourceNamesList(CustomWidget):

    def __init__(self, window, row, col, **kwargs):
        CustomWidget.__init__(self, window, row, col, **kwargs)
        self.json_path = 'forms/resource_names.json'
        self.names = []
        self.load_json()
        self.entry = Entry(self.window)
        self.entry.grid(row=self.row, column=self.col)
        self.add_button = Button(self.window, text='Add', command=self.add_name)
        self.add_button.grid(row=self.row, column=self.col + 1)
        # Listbox
        self.relevant_resource_names_listbox = Listbox(self.window)
        self.relevant_resource_names_listbox.grid(row=self.row + 1, column=self.col)
        for val in self.load_json():
            self.relevant_resource_names_listbox.insert(END, val)

    def load_json(self):
        try:
            return json.loads(open(self.json_path, 'r').read())
        except ValueError:
            return []

    def add_name(self):
        self.names.append(self.entry.get())
        self.save_json()
        self.relevant_resource_names_listbox.insert(END, self.entry.get())

    def save_json(self):
        old_names = self.load_json()
        f = open(self.json_path, 'w')
        f.write(json.dumps(old_names + self.names))

if __name__ == '__main__':
    pass
