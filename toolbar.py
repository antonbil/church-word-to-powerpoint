import PySimpleGUI as sg

class ToolBar:
    """header dialog class"""
    def __init__(self):
        self.button_nr = 0
        self.button_ids = {}

    def get_button_id(self, button):
        if button in self.button_ids:
            return self.button_ids[button]
        if button in self.button_ids.values():
            return button
        return "Nonsense..."

    def buttonbar_add_buttons(self, window, buttons):
        for child in window.find_element('button_frame').widget.winfo_children():
            #print("child:", child)
            child.destroy()
        window.extend_layout(window['button_frame'], [buttons])
        window.Refresh()

    def new_button(self, title, auto_size_button=False):
        self.button_nr = self.button_nr + 1
        id = "_id{}_".format(self.button_nr)
        self.button_ids[id] = title
        return sg.Button(title, key=id, auto_size_button=auto_size_button)
