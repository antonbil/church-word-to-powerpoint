import PySimpleGUI as sg

class ToolBar:
    """header dialog class"""
    def __init__(self, text_font, bar_id='button_frame'):
        self.button_nr = 0
        self.button_ids = {}
        self.text_font = text_font
        self.bar_id = bar_id

    def get_button_id(self, button):
        try:
            button = "_"+button.split('_')[1]+"_"
        except:
            return "Nonsense..."
        if button == "__TIMEOUT__":
            return "Nonsense..."
        if button in self.button_ids:
            #print("button found", self.button_ids)
            return self.button_ids[button]
        if button in self.button_ids.values():
            #print("value found", self.button_ids.values())
            return button
        return "Nonsense..."

    def buttonbar_add_buttons(self, window, buttons):
        for child in window.find_element(self.bar_id).widget.winfo_children():
            #print("child:", child)
            child.destroy()
        window.extend_layout(window[self.bar_id], [buttons])
        window.Refresh()

    def new_button(self, title, auto_size_button=False):
        self.button_nr = self.button_nr + 1
        id = "_id{}_".format(self.button_nr)
        self.button_ids[id] = title
        return sg.Button(title, key=id, auto_size_button=auto_size_button, font=self.text_font)
