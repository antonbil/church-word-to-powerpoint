# sermon_create.py
from docx.shared import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt
import io


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
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        slide_layout = self.powerpoint_presentation.slide_layouts[0]  # Assuming you want to use the first slide layout from the template
        is_first_slide = True

        last_bottom = 0
        previous_text = None
        for hymn in hymn_data:
            if not (last_bottom > 0 and hymn["text"]) and not (previous_text and hymn["text"]):
                slide = self.add_slide(slide_layout)

            # Add title (only on the first slide)
            if title and is_first_slide:
                self.set_title(slide, title)

                is_first_slide = False
            # add content (only image or text)
            if len(hymn["images"]) > 0:
                # Image formatting
                image_width = Inches(self.settings.get_setting("powerpoint-image_width"))
                image_height = Inches(self.settings.get_setting("powerpoint-image_height"))
                image_left = Inches(self.settings.get_setting("powerpoint-image_left"))  # Fixed left offset
                image_top = Inches(self.settings.get_setting("powerpoint-image_top")) # Fixed top offset
                image_bytes = hymn["images"][0]
                image_stream = io.BytesIO(image_bytes)
                picture = slide.shapes.add_picture(image_stream, left=image_left, top=image_top, width=image_width)
                last_bottom = picture.top + picture.height

            elif hymn["text"]:
                i = 0
                for p in slide.placeholders:
                    if i==1:
                        if last_bottom > 0:
                            left = p.left
                            p.top = p.top + last_bottom - 200
                            p.left = left
                            previous_text = None
                            p.text = hymn["text"]
                        else:
                            if previous_text:
                                p.text = p.text + "\n\n" + hymn["text"]
                                previous_text = None
                            else:
                                p.text = hymn["text"]
                                previous_text = p
                        # Set content text color to white
                        for paragraph in p.text_frame.paragraphs:
                            self.set_color_text_line(paragraph)
                            paragraph.font.size = Pt(self.settings.get_setting("powerpoint-content_font_size"))
                        # set the text at the top:
                        p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
                        last_bottom = 0
                    i = i + 1
        self.create_empty_slide()

    def add_slide(self, slide_layout):
        slide = self.powerpoint_presentation.slides.add_slide(slide_layout)
        return slide

    def set_color_text_line(self, paragraph):
        color = self.settings.get_setting("powerpoint-content_font_color")
        paragraph.font.color.rgb = RGBColor(color["red"], color["green"], color["blue"])

    def create_outro_slides(self, date, parson, performed_piece = None):
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

        slide_layout = self.powerpoint_presentation.slide_layouts[0]
        slide = self.add_slide(slide_layout)

        # Set the title
        title_text = self.settings.get_setting("powerpoint-outro_title")
        if performed_piece:
            title_text = performed_piece
        def extra_layout_func(paragraph, line_number):
            paragraph.alignment = PP_ALIGN.CENTER

        self.set_title(slide, title_text, extra_layout_func)

        # Set the content
        next_service_line = self.settings.get_setting("powerpoint-outro_next_service_line")
        parson_line = self.settings.get_setting("powerpoint-outro_parson_line") #new
        content_text = f"{next_service_line}:\n\n{date} \n\n{parson_line}:\n{parson}"
        self.format_placeholder_text(1, content_text, slide)

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

        slide_layout = self.powerpoint_presentation.slide_layouts[0]
        slide = self.add_slide(slide_layout)

        # Set the content
        first_goal_label = self.settings.get_setting("powerpoint-offering_first_goal_label")
        second_goal_label = self.settings.get_setting("powerpoint-offering_second_goal_label")
        output = [first_goal_label, offering_data['offering_goal' ], offering_data["bank_account_number" ], "\n", second_goal_label]
        content_text = "\n".join(output)
        content_text_list = content_text.split("\n")
        empty_item = self.find_first_empty_string_index(content_text_list) + 2

        # add content to slide
        def extra_layout_func(paragraph, line_number):
            paragraph.font.underline = (True if line_number == 0 or line_number == empty_item else False)
        self.format_placeholder_text(1, content_text, slide, extra_layout_func)
        self.create_empty_slide()


    def create_intro_slides(self, intro_data):
        """
        Creates the intro slide.

        Args:
            intro_data (dict): The data of the intro (dict).
        """
        print("create_intro_slides")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        slide_layout = self.powerpoint_presentation.slide_layouts[0]
        slide = self.add_slide(slide_layout)

        # Set the title
        title_text = self.settings.get_setting("powerpoint-intro_title")
        def extra_layout_func(paragraph, line_number):
            paragraph.alignment = PP_ALIGN.CENTER
        self.set_title(slide, title_text, extra_layout_func)

        performed_piece = ""
        # Set the content
        intro_lines = []
        if "date" in intro_data:
            intro_lines.append(f"{intro_data['date']}")
        if "parson" in intro_data:
            intro_lines.append(f"\n{self.settings.get_setting('word-intro-parson_label')}\n{intro_data['parson']}\n")
        if "theme" in intro_data:
            intro_lines.append(f"\n{self.settings.get_setting('word-intro-theme_label')}\n{intro_data['theme']}\n")
        if "organist" in intro_data:
            intro_lines.append(f"\n{self.settings.get_setting('word-intro-organist_label')}\n{intro_data['organist']}")
        if "performed_piece" in intro_data:
            performed_piece = intro_data['performed_piece']
        content_text = "\n".join(intro_lines)

        #add content to slide
        self.format_placeholder_text(1, content_text, slide)

        self.duplicate_slide_with_layout(slide, self.settings.get_setting('slide-layout-intro-2'), extra_layout_func)
        third_slide = self.duplicate_slide_with_layout(slide, self.settings.get_setting('slide-layout-intro-2'), extra_layout_func)
        # set title to performed_piece
        if performed_piece:
            self.set_title(third_slide, performed_piece, extra_layout_func)
        self.create_empty_slide()

    def create_illustration_slides(self, image_data):
        """
        Creates a slide for the illustration section, displaying the image.

        Args:
            image (tuple): A tuple containing (image_data, image_content_type) or (None, None) if no illustration is found.
        """
        print("create_illustration_slides")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        if image_data is not None:
            slide_layout = self.powerpoint_presentation.slide_layouts[0]
            slide = self.add_slide(slide_layout)
            # Remove the title-placeholder
            for shp in slide.placeholders:
                if shp.name.startswith(self.settings.get_setting("placeholder-title-name")):
                    sp = shp.element
                    sp.getparent().remove(sp)
            # Add image to the slide
            image_width = Inches(self.settings.get_setting("image_width"))
            image_height = Inches(self.settings.get_setting("image_height"))
            image_left = Inches(self.settings.get_setting("image_left"))  # Fixed left offset
            image_top = Inches(self.settings.get_setting("image_top"))  # Fixed top offset
            image_stream = io.BytesIO(image_data)
            try:
                slide.shapes.add_picture(image_stream, left=image_left, top=image_top, width=image_width, height=image_height)
            except Exception as e:
                print("An error occured while adding the picture: ", e)

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
                    self.set_color_text_line(paragraph)
                    paragraph.font.size = Pt(self.settings.get_setting("powerpoint-content_font_size"))
                    # align the entire paragraph in the middle
                    paragraph.alignment = PP_ALIGN.CENTER
                    if custom_formatter:
                        custom_formatter(paragraph, line_number)

                # set the text at the top:
                p.text_frame.vertical_anchor = MSO_ANCHOR.TOP

    def set_title(self, slide, title_text, custom_formatter=None):
        try:
            title_placeholder = slide.shapes.title
            # print(title_text)
            title_placeholder.text = title_text  # modified
            for line_number, paragraph in enumerate( title_placeholder.text_frame.paragraphs):
                self.set_color_text_line(paragraph)
                paragraph.font.size = Pt(self.settings.get_setting("title_font_size"))
                if custom_formatter:
                    custom_formatter(paragraph, line_number)
        except:
            pass


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

    def create_empty_slide(self):
        slide_layout = self.powerpoint_presentation.slide_layouts[0]
        slide = self.add_slide(slide_layout)

