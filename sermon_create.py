from docx.shared import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
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
                slide = self.powerpoint_presentation.slides.add_slide(slide_layout)

            # Add title (only on the first slide)
            if title and is_first_slide:
                title_placeholder = slide.shapes.title
                title_placeholder.text = title
                # Set title text color to white
                for paragraph in title_placeholder.text_frame.paragraphs:
                    paragraph.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) # White
                    paragraph.font.size = Pt(self.settings.get_setting("title_font_size"))
                is_first_slide = False
            # add content (only image or text)
            if len(hymn["images"]) > 0:
                # Image formatting
                image_width = Inches(self.settings.get_setting("image_width"))
                image_height = Inches(self.settings.get_setting("image_height"))
                image_left = Inches(self.settings.get_setting("image_left"))  # Fixed left offset
                image_top = Inches(self.settings.get_setting("image_top")) # Fixed top offset
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
                            paragraph.font.color.rgb = RGBColor(self.settings.get_setting("content_font_color")["red"], self.settings.get_setting("content_font_color")["green"], self.settings.get_setting("content_font_color")["blue"]) # White
                            paragraph.font.size = Pt(self.settings.get_setting("content_font_size"))
                        # set the text at the top:
                        p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
                        last_bottom = 0
                    i = i + 1

    def create_outro_slides(self, date, parson):
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
        slide = self.powerpoint_presentation.slides.add_slide(slide_layout)

        # Set the title
        title_text = self.settings.get_setting("outro_title") #new
        title_placeholder = slide.shapes.title
        title_placeholder.text = title_text #modified
        for paragraph in title_placeholder.text_frame.paragraphs:
            paragraph.font.color.rgb = RGBColor(self.settings.get_setting("title_font_color")["red"], self.settings.get_setting("title_font_color")["green"], self.settings.get_setting("title_font_color")["blue"])  # White
            paragraph.font.size = Pt(self.settings.get_setting("title_font_size"))

        # Set the content
        next_service_line = self.settings.get_setting("outro_next_service_line") #new
        parson_line = self.settings.get_setting("outro_parson_line") #new
        content_text = f"{next_service_line}:\n\n{date} \n\n{parson_line}:\n{parson}" #modified

        i = 0
        for p in slide.placeholders:
            if i == 1:
                p.text = content_text
                # Set content text color to white
                for paragraph in p.text_frame.paragraphs:
                    paragraph.font.color.rgb = RGBColor(self.settings.get_setting("content_font_color")["red"], self.settings.get_setting("content_font_color")["green"], self.settings.get_setting("content_font_color")["blue"]) # White
                    paragraph.font.size = Pt(self.settings.get_setting("content_font_size"))
                # set the text at the top:
                p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
            i += 1