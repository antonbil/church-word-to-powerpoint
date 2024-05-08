import PySimpleGUI as sg
import os.path


class InputDialog:
    def __init__(self, gui, default_png_dir):
        self.shift = False
        self.chars = []
        self.filename = ""
        self.gui = gui
        self.default_png_dir = default_png_dir

    def read_file(self):
        #  Define Layout 
        fnames = self._file_list(self.default_png_dir)
        left_col = [self.get_folder_elements(),
                    [sg.Listbox(values=fnames, enable_events=True, size=(40, 20), key='-FILE LIST-',
                                font=self.gui.text_font, sbar_width=self.gui.scrollbar_width,
                                sbar_arrow_width=self.gui.scrollbar_width
                                )]]
        layout = [[left_col],
                  self.get_buttons()]
        folder = self.default_png_dir

        # Create Window
        window = sg.Window('Read PGN', layout)

        #  Run the Event Loop
        filename = ""
        self.filename = ""
        while True:
            event, values = window.Read(timeout=50)
            if event in (None, 'Exit'):
                break
            if event == '-FOLDER-':  # Folder name was filled in, make a list of files in the folder
                folder = values['-FOLDER-']
                fnames = self._file_list(folder)
                window['-FILE LIST-'].update(fnames)
            elif event == '-FILE LIST-':  # A file was chosen from the listbox
                try:
                    filename = os.path.join(values['-FOLDER-'], values['-FILE LIST-'][0])

                except:
                    pass  # something weird happened making the full filename
            elif event == "OK":
                self.filename = filename
                window.close()
                break
            elif event == "Set Default Dir":
                self.save_default_folder(folder)
            elif event == "Close":
                window.close()
                break

    def get_folder_elements(self):
        return [sg.Text('Folder', font=self.gui.text_font),
                sg.In(self.default_png_dir, font=self.gui.text_font, size=(25, 1), enable_events=True, key='-FOLDER-'),
                sg.FolderBrowse(initial_folder=self.default_png_dir, font=self.gui.text_font)]

    def save_file(self, file_name):
        #  Define Layout 
        left_col = [self.get_folder_elements(),
                    [sg.Text('File', font=self.gui.text_font),
                     sg.In(file_name, font=self.gui.text_font, size=(25, 1), enable_events=True,
                           key='-FILE-')]]
        layout = [[left_col],
                  self.get_buttons()]

        folder = self.default_png_dir
        #  Create Window 
        window = sg.Window('Save PGN', layout)

        #  Run the Event Loop
        self.filename = ""
        while True:
            event, values = window.Read(timeout=50)
            if event in (None, 'Exit'):
                break
            if event == '-FOLDER-':
                folder = values['-FOLDER-']
            elif event == "OK":
                self.filename = os.path.join(values['-FOLDER-'], values['-FILE-'])
                window.close()
                break
            elif event == "Set Default Dir":
                self.save_default_folder(folder)
            elif event == "Close":
                window.close()
                break

    def get_buttons(self):
        return [sg.Button("OK", font=self.gui.text_font), sg.Button("Close", font=self.gui.text_font),
            sg.Button("Set Default Dir", font=self.gui.text_font)]

    def save_default_folder(self, folder):
        self.gui.preferences.preferences["default_png_dir"] = folder
        self.gui.default_png_dir = folder
        self.gui.preferences.save_preferences()

    def _file_list(self, folder):
        try:
            file_list = os.listdir(folder)  # get list of files in folder
        except:
            file_list = []
        fnames = [f for f in file_list if os.path.isfile(
            os.path.join(folder, f)) and f.lower().endswith(".pgn")]
        fnames.sort()
        return fnames

    def get_keyboard_keys(self, sg, gui):
        keys = ["QWERTYUIOP", "ASDFGHJKL\n", "ZXCVBNM,.", " "]
        self.chars = ''.join(keys)
        lines = list(map(list, keys))
        # two keys which have specific behaviour
        lines[1].insert(0, "\u21E7")  # U+21E7 shift
        lines[0] += ["\u232B", "Esc"]  # backspace
        # space and return are visualized different on the visual keys itself
        visual_keys = {" ": "          ", "\n": "\u2386"}
        col = [[sg.Push()] + [sg.Button(visual_keys[key] if key in visual_keys else key,
                                        key=key, font=gui.text_font) for key in line] + [sg.Push()] for line in lines]
        return [sg.pin(sg.Column(col, visible=False, expand_x=True, key='Column', metadata=False), expand_x=True)]

    def get_keyboard_button(self, sg, gui):
        return sg.Button("Keyboard", font=gui.text_font)

    def select_present(self, widget):
        if hasattr(widget, 'select_present'):
            # multi-line has no method: select_present
            return widget.select_present()
        else:
            return False

    def check_keyboard_input(self, window, event):
        if event == "Keyboard":
            keyboard = window.find_element("Column")
            visible = keyboard.metadata = not keyboard.metadata
            keyboard.update(visible=visible)
        elif event in self.chars:
            element = window.find_element_with_focus()
            key = event
            if not self.shift:
                key = key.lower()
            if isinstance(element, sg.Input) or isinstance(element, sg.Multiline):
                if self.select_present(element.widget):
                    element.widget.delete(sg.tk.SEL_FIRST, sg.tk.SEL_LAST)
            element.widget.insert(sg.tk.INSERT, key)
            self.shift = False
        elif event == "\u232B":
            element = window.find_element_with_focus()
            if self.select_present(element.widget):
                element.widget.delete(sg.tk.SEL_FIRST, sg.tk.SEL_LAST)
            else:
                insert = element.widget.index(sg.tk.INSERT)
                # in multiline widget this can be: 1.49 (line 1, char 49)
                print("insert", insert)
                try:
                    if insert > 0:
                        element.widget.delete(insert - 1, insert)
                except:
                    # multiline?
                    try:
                        splits = insert.split(".")
                        pos = int(splits[1])
                        if pos > 0:
                            element.widget.delete("{}.{}".format(splits[0], pos - 1), insert)
                    except:
                        pass
        elif event == "\u21E7":
            self.shift = True

    def popup_get_text(self, sg,gui,message, title="", default_text=""):
        my_key = '_InputValue_'

        layout = [[sg.Text(message, size=(len(message), 1), font=gui.text_font),
               sg.InputText(default_text, font=gui.text_font, key=my_key,
                            size=(50, 1))],
              [sg.Button("OK", font=gui.text_font),
               sg.Button("Cancel", font=gui.text_font), sg.Push(), self.get_keyboard_button(sg, gui)],
              self.get_keyboard_keys(sg, gui)
              ]
        window = sg.Window(title, layout, font=gui.text_font,
                           finalize=True, modal=True, keep_on_top=True)
        ret_value = ""
        while True:
            event, values = window.read()
            if event in ("Cancel", sg.WIN_CLOSED):
                break
            self.check_keyboard_input(window, event)

            if event == "OK":
                ret_value = values[my_key]
                break
            if event == "Cancel":
                break
        window.close()
        return ret_value

    def get_comment(self, current_move, gui):
        """
        get comment for current move
        :param current_move:
        :param gui:
        :return:
        """
        layout = [[sg.Multiline(current_move.comment, key='Comment', font=gui.text_font
                                , size=(60, 10))],
                  [sg.Button('OK', font=gui.text_font), sg.Cancel(font=gui.text_font), sg.Push(),
                   self.get_keyboard_button(sg, gui)], self.get_keyboard_keys(sg, gui)
                  ]
        window = sg.Window('Enter comment', layout, finalize=True, modal=True, keep_on_top=True)
        ok = False
        while True:
            event, values = window.read()
            if event == "Cancel" or event == sg.WIN_CLOSED or event == 'Exit':
                break
            self.check_keyboard_input(window, event)
            if event == "OK":
                comment = values['Comment']
                ok = True
                current_move.comment = comment.strip()

                break
        window.close()
        return ok


