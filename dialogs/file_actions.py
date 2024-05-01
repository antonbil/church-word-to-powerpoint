import PySimpleGUI as sg
import os.path


class FileDialog:
    def __init__(self, gui, default_png_dir):
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

    def get_comment(self, current_move, gui):
        layout = [[sg.Multiline(current_move.comment, key='Comment', font=gui.text_font
                                , size=(60, 10))],
                  [sg.Button('OK', font=gui.text_font), sg.Cancel(font=gui.text_font)]
                  ]
        window = sg.Window('Enter comment', layout, finalize=True)
        ok = False
        while True:
            event, values = window.read()
            if event == "Cancel" or event == sg.WIN_CLOSED or event == 'Exit':
                break
            if event == "OK":
                comment = values['Comment']
                ok = True
                current_move.comment = comment.strip()

                break
        window.close()
        return ok


