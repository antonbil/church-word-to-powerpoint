# sermon_create.py
from docx.shared import Pt
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt


class SermonCreate:
    """
    Contains the methods for creating PowerPoint slides.
    """
    def create_hymn_slides(self, title, hymn_data):
        """
        Creates PowerPoint slides for the hymn sections using a template.

        Args:
            title (str): The title of the hymn section (or None if no title).
            hymn_data (list): A list of dictionaries containing hymn data (text and images).
        """
        print("add hymn-data")
        #create hymn-data to make code more clear
        image_list = [h["images"][0]for h in hymn_data if len(h["images"]) > 0]
        hymn_parts = [hymn["text"] for hymn in hymn_data if hymn["text"]]
        #local function to get the number of lines in a string
        def get_number_lines(string):
            return len(string.split("\n"))
        template_id = "slide-layout-lied"
        original_template_id = template_id
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return
        is_first_slide = True

        song_length_first = self.settings.get_setting("powerpoint-hymn-song-length-first")
        song_length_first_image = self.settings.get_setting("powerpoint-hymn-song-length-first-image")
        song_length_rest = self.settings.get_setting("powerpoint-hymn-song-length-rest")
        current_song_length = song_length_first
        current_length = 0

        image = None
        if len(image_list) > 0:
            image = image_list[0]
            template_id = template_id + "-image"
            current_song_length = song_length_first_image

        for hymn_part in hymn_parts:
            if get_number_lines(hymn_part) + current_length > current_song_length or is_first_slide:
                slide = self.add_slide(template_id)
                if not is_first_slide:
                    current_song_length = song_length_rest

            # Add title (only on the first slide)
            if title and is_first_slide:
                self.set_title(slide, title)

            is_first_slide = False
            template_id = original_template_id + "-no-title"

            # add image to slide if it exists
            if image:
                # Image creation and formatting
                self._add_image_to_slide(image, slide)
                image = None

            # add hymn-part to slide
            for i, p in enumerate(slide.placeholders):
                if i==1:
                    if get_number_lines(hymn_part) + current_length > current_song_length:
                        p.text = hymn_part
                    else:
                        p.text = (p.text + "\n\n" + hymn_part).strip()
                    current_length = get_number_lines(p.text)

                    # Set content text appearance
                    for paragraph in p.text_frame.paragraphs:
                        self.set_text_appearance(paragraph)
                    # set the text at the top:
                    p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
        self.create_empty_slide()

    def create_reading_slides(self, title, reading_data):
        """
        Creates PowerPoint slides for the reading sections using a template.

        Args:
            title (str): The title of the reading section (or None if no title).
            reading_data (list): A list of dictionaries containing reading data (text and images).
        """
        print("add reading-data")
        template_id = "slide-layout-reading"
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return
        is_first_slide = True

        for reading in reading_data:
            slide = self.add_slide(template_id)

            # Add title (only on the first slide)
            if title and is_first_slide:
                self.set_title(slide, title)

                is_first_slide = False
                template_id = template_id + "-no-title"

            # find second placeholder
            i = 0
            for p in slide.placeholders:
                if i==1:
                    p.text = reading["text"]
                    # Set content text color to white
                    for paragraph in p.text_frame.paragraphs:
                        self.set_text_appearance(paragraph)
                    # set the text at the top:
                    p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
                i = i + 1
        self.create_empty_slide()

    def create_outro_slides(self, date, parson, template_id, performed_piece = None):
        """
        Creates the outro slide.

        Args:
            date (str): The date of the next service.
            parson (str): The name of the parson.
        """
        print("create_outro_slides")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        slide = self.add_slide(template_id)

        # Set the title
        title_text = self.settings.get_setting("powerpoint-outro_title")
        if performed_piece:
            title_text = performed_piece

        def extra_layout_func(paragraph, line_number):
            paragraph.alignment = PP_ALIGN.CENTER

        self.set_title(slide, title_text, extra_layout_func)

        def content_layout_func(paragraph, line_number):
            paragraph.alignment = PP_ALIGN.CENTER
            font_size = self.settings.get_setting('powerpoint-outro_font_size')
            paragraph.font.size = Pt(font_size)
            paragraph.font.italic = True
            paragraph.font.bold = False

        # Set the content
        next_service_line = self.settings.get_setting("powerpoint-outro_next_service_line")
        parson_line = self.settings.get_setting("powerpoint-outro_parson_line") #new
        content_text = f"{next_service_line}:\n\n{date} \n\n{parson_line}:\n{parson}"
        self.format_placeholder_text(1, content_text, slide, content_layout_func)

    def create_offering_slides(self, offering_data):
        """
        Creates the offering slide.

        Args:
            offering_data (list): The data of the offering (list).
        """
        print("create_offering_slides")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        slide = self.add_slide("slide-layout-offering")

        # Set the content
        first_goal_label = self.settings.get_setting("powerpoint-offering_first_goal_label")
        second_goal_label = self.settings.get_setting("powerpoint-offering_second_goal_label")
        output = [first_goal_label, offering_data['offering_goal' ], offering_data["bank_account_number" ], "", second_goal_label]
        content_text = "\n".join(output)
        content_text_list = content_text.split("\n")
        empty_item = self.find_first_empty_string_index(content_text_list) + 2

        # add content to slide
        def extra_layout_func(paragraph, line_number):
            paragraph.font.underline = (True if line_number == 0 or line_number == empty_item else False)
            font_size = self.settings.get_setting('powerpoint-offering_font_size')
            paragraph.font.size = Pt(font_size)
            paragraph.font.italic = True
            paragraph.font.bold = False

        self.format_placeholder_text(1, content_text, slide, extra_layout_func)
        self.create_empty_slide()


    def create_intro_slides(self, intro_data, template_id, performed_piece_in_title = False):
        """
        Creates the intro slide.

        Args:
            intro_data (dict): The data of the intro (dict).
        """
        print("create_intro_slide")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        slide = self.add_slide(template_id)

        # Set the title
        title_text = self.settings.get_setting("powerpoint-intro_title")
        def extra_layout_func(paragraph, line_number):
            paragraph.alignment = PP_ALIGN.CENTER
        self.set_title(slide, title_text, extra_layout_func)

        performed_piece = ""
        intro_template = self.settings.get_setting('powerpoint-intro_template')

        for id in ["date", "parson", "theme", "organist"]:
            try:
                index = intro_template.index("{" + id + "}")
                if id in intro_data and index >= 0:
                    intro_template[index] = intro_template[index].replace("{" + id + "}", intro_data[id])
                else:
                    intro_template.pop(index)  # Remove the placeholder
                    if index > 0 and intro_template[index - 1].strip() != "":
                        # Remove the heading-line if the previous line is not empty
                        intro_template.pop(index - 1)
                    elif index > 0:
                        # remove the empty heading line
                        intro_template.pop(index - 1)
            except ValueError:
                pass

        # Set the content
        intro_lines = intro_template
        if "performed_piece" in intro_data:
            performed_piece = intro_data['performed_piece']
        content_text = "\n".join(intro_lines)

        def extra_layout_func(paragraph, line_number):
            font_size = self.settings.get_setting('powerpoint-intro_font_size')
            paragraph.font.size = Pt(font_size)
            paragraph.font.italic = True
            paragraph.font.bold = False
        #add content to slide
        self.format_placeholder_text(1, content_text, slide, extra_layout_func)

        # set title to performed_piece
        if performed_piece and performed_piece_in_title:
            self.set_title(slide, performed_piece, extra_layout_func)


    def create_illustration_slides(self, image_data):
        """
        Creates a slide for the illustration section, displaying the image.

        Args:
            image_data: the image for the illustration-slide
        """
        print("create_illustration_slides")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        if image_data is not None:
            slide = self.add_slide("slide-layout-intro-2")
            # Remove the title-placeholder
            for shp in slide.placeholders:
                if shp.name.startswith(self.settings.get_setting("placeholder-title-name")):
                    sp = shp.element
                    sp.getparent().remove(sp)
            self._add_image_to_slide(image_data, slide, setting_id = "illustration")

            self.create_empty_slide()

    def format_placeholder_text(self, placeholder_index, content_text, slide, custom_formatter=None):
        """
        Formats the text within a placeholder with the specified settings.

        Args:
            placeholder_index: the index of the placeholder.
            content_text: the text to put in the placeholder.
            slide: the current slide.
            custom_formatter: An optional callable (e.g., lambda) that takes a paragraph
                              and the line number as arguments for custom formatting.
        """
        for i, p in enumerate(slide.placeholders):
            if i == placeholder_index:
                p.text = content_text

                for line_number, paragraph in enumerate(p.text_frame.paragraphs):
                    self.set_text_appearance(paragraph)
                    # align the entire paragraph in the middle
                    paragraph.alignment = PP_ALIGN.CENTER
                    if custom_formatter:
                        custom_formatter(paragraph, line_number)

                # set the text at the top:
                p.text_frame.vertical_anchor = MSO_ANCHOR.TOP

    def find_first_empty_string_index(self, string_list):
        """
        Finds the index of the first empty string in a list of strings.

        Args:
          string_list: A list of strings.

        Returns:
          The index of the first empty string, or None if no empty string is found.
        """
        for index, item in enumerate(string_list):
            if not item:
                return index
        return None  # Return None if no empty string is found

    def add_slide(self, slide_layout_code):
        """
        Add slide to the current powerpoint-presentation.

        Args:
            slide_layout (layout-from-template): The layout that is used.
        """

        slide_layout = self.settings.get_setting(slide_layout_code)

        # layout = None
        # for layout_idx, slide_layout1 in enumerate(self.powerpoint_presentation.slide_layouts):
        #     if layout_idx == slide_layout:
        #         print(f"\nSlide Layout {layout_idx}: {slide_layout1.name}")
        #         layout = slide_layout1

        slide = self.powerpoint_presentation.slides.add_slide(self.powerpoint_presentation.slide_layouts[slide_layout])
        return slide

    def create_empty_slide(self):
        """
        create empty slide based on default empty template-slide
        """
        self.add_slide("slide-layout-empty")

