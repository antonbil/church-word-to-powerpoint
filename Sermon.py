from docx import Document
from docx.shared import Pt, Inches
from pptx import Presentation
from pptx.util import Inches
import os
import io
import re
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR

class Sermon:
    """
    Represents a church service and handles the creation of a PowerPoint presentation
    from a Word document order of service.
    """

    def __init__(self, word_filename):
        """
        Initializes the Sermon object with the path to the Word document.

        Args:
            word_filename (str): The filename of the Word document (e.g., "orde-van-dienst.docx").
        """
        self.word_filename = word_filename
        self.max_reading_lines = 20
        self.powerpoint_filename = os.path.splitext(word_filename)[0] + ".pptx"
        self.word_document = None
        self.powerpoint_presentation = None
        # current_paragraph_index is the pointer to the current paragraph in the Word-file
        self.current_paragraph_index = 0
        self.num_paragraphs = 0
        # Define the tags
        self.tags = {
            "hymn": {"begin": "[Li]", "end": ["[/Li]", "[Li]", "Moment van inkeer:", "Woorden van vertrouwen"]},
            "collection": {"begin": "begin-collecte-tag", "end": ["eind-collecte-tag"]},
            "intro": {"begin": "begin-intro-tag", "end": ["eind-intro-tag"]},
            "reading": {"begin": "[Le]", "end": ["[/Le]", "Overdenking:"]},
            "organ": {"begin": "begin-orgelspel-tag", "end": ["eind-orgelspel-tag"]},
            "outro": {"begin": "begin-outro-tag", "end": ["eind-outro-tag"]}
        }
        self.current_tag = None

    def load_word_document(self):
        """
        Loads the Word document and handles potential errors.
        """
        try:
            self.word_document = Document(self.word_filename)
        except FileNotFoundError:
            print(f"Error: Word document '{self.word_filename}' not found.")
            self.word_document = None
        except Exception as e:
            print(f"An unexpected error occurred while loading the Word document: {e}")
            self.word_document = None

    def create_powerpoint_presentation(self):
        """
        Creates an empty PowerPoint presentation with the specified filename.
        """
        try:
            # Load the template
            self.powerpoint_presentation = Presentation('orde-van-dienst-template.pptx')
            self.powerpoint_presentation.save(self.powerpoint_filename)
        except Exception as e:
            print(f"An unexpected error occurred while creating the PowerPoint presentation: {e}")
            self.powerpoint_presentation = None

    def process_sermon(self):
        """
        Main method to process the sermon data and create the PowerPoint.
        Iterates through the paragraphs in the Word document using a while loop
        and a pointer, identifying start tags and calling the appropriate extraction
        functions.
        """
        self.load_word_document()
        if self.word_document is None:
            return  # Stop processing if there was an error loading the Word document

        self.create_powerpoint_presentation()
        if self.powerpoint_presentation is None:
            return

        paragraphs = self.word_document.paragraphs
        self.num_paragraphs = len(paragraphs)
        self.current_paragraph_index = 0
        #print(self.word_document.paragraphs)
        print(self.num_paragraphs)
        # print(f"Number of paragraphs: {len(self.word_document.paragraphs)}")
        # for count, para in enumerate(self.word_document.paragraphs, start=1):
        #     print(f"{count}: {para.text}")

        while self.current_paragraph_index < self.num_paragraphs:
            paragraph = self.word_document.paragraphs[self.current_paragraph_index]
            is_start_tag = False
            for tag_type, tag_data in self.tags.items():
                if tag_data["begin"] in paragraph.text:
                    is_start_tag = True

                    self.current_tag = tag_type

                    # Process the current section
                    if self.current_tag == "hymn":
                        title, hymn_data = self.extract_hymn_section(paragraphs[self.current_paragraph_index:])
                        self.create_hymn_slides(title, hymn_data)
                    elif self.current_tag == "collection":
                        collection_data = self.extract_collection_section(paragraphs[self.current_paragraph_index:])
                        # self.create_collection_slides(collection_data)
                    elif self.current_tag == "intro":
                        intro_data = self.extract_intro_section(paragraphs[self.current_paragraph_index:])
                        # self.create_intro_slides(intro_data)
                    elif self.current_tag == "reading":
                        title, reading_data = self.extract_reading_section(paragraphs[self.current_paragraph_index:])
                        print(reading_data)
                        self.create_hymn_slides(title, reading_data)
                    elif self.current_tag == "organ":
                        organ_data = self.extract_organ_section(paragraphs[self.current_paragraph_index:])
                        # self.create_organ_slides(organ_data)
                    elif self.current_tag == "outro":
                        outro_data = self.extract_outro_section(paragraphs[self.current_paragraph_index:])
                        # self.create_outro_slides(outro_data)

            if not is_start_tag:
                self.current_paragraph_index += 1

        self.powerpoint_presentation.save(self.powerpoint_filename)
        if self.powerpoint_presentation is None:
            return

        print(f"PowerPoint presentation '{self.powerpoint_filename}' created successfully.")

    def extract_hymn_section(self, paragraphs):
        """
        Extracts the hymn section, including title, and all hymns within the section
        (text and images) from a list of paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (title, hymn_data)
                   title (str or None): The title of the hymn section (or None if no title).
                   hymn_data (list): A list of dictionaries, where each dictionary represents a
                                     hymn and contains its text and image data.
        """
        hymn_data = []
        current_text = []
        title = None
        new_index = 0
        in_hymn_section = False
        index = -1
        print("check for hymn sections")
        print(self.current_paragraph_index)

        # check if the hymn-section has a title:
        if len(paragraphs) > 0:
            in_hymn_section, index, title = self.get_hymn_title(index, paragraphs)
        while self.current_paragraph_index + index < self.num_paragraphs-1:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]

            if self.tags["hymn"]["begin"] in paragraph.text:
                # a new hymn is started
                in_hymn_section = True
                continue
            if self.check_end_tag("hymn", paragraph):
                # no hymn, but a next hymn can be possible
                in_hymn_section = False
                if len(current_text) > 0:
                    paragraph_data = {"text": "\n".join(current_text), "images": []}
                    hymn_data.append(paragraph_data)
                current_text = []
                new_index = index + 1
                continue
            if len(paragraph.text.strip()) == 0 and not in_hymn_section:
                # empty line; skip
                new_index = index
                continue
            if len(paragraph.text.strip()) > 0 and not in_hymn_section:
                # not next hymn, so the hymn-section is finished
                new_index = index
                break
            if in_hymn_section:
                self.extract_paragraph_content(paragraph)
                print(paragraph.text)
                if len(paragraph.text) > 0:
                    current_text.append(paragraph.text)

                # check if the hymn-section starts with a picture:
                if len(hymn_data) == 0:
                    # if first paragraph in hymn-section contains an image, this is considered as a 'hymn'
                    self.get_hymn_image(hymn_data, paragraph)
        self.current_paragraph_index = self.current_paragraph_index + new_index
        return title, hymn_data

    def check_end_tag(self, tag, paragraph):
        """
        Checks if any of the defined end tags for the given tag are present in the paragraph.

        Args:
            tag (str): The tag to check (e.g., "hymn", "reading").
            paragraph (docx.paragraph.Paragraph): The paragraph to check.

        Returns:
            bool: True if any of the end tags are found, False otherwise.
        """
        for end_tag in self.tags[tag]["end"]:
            if end_tag.lower() in paragraph.text.lower():
                return True
        return False

    def get_hymn_title(self, index, paragraphs):
        title = None
        in_hymn_section = False
        first_paragraph = paragraphs[0]
        # check if the first paragraph contains a title:
        if first_paragraph.runs and first_paragraph.runs[0].bold:
            title = first_paragraph.text
            if self.tags["hymn"]["begin"] in title:
                title = title.replace(self.tags["hymn"]["begin"], "")
                in_hymn_section = True
            # check if this is a two-line title
            if len(paragraphs) > 1:
                second_paragraph = paragraphs[1]
                # check if the second paragraph is also part of the title.
                if second_paragraph.runs and second_paragraph.runs[0].bold:
                    title = title + "\n" + second_paragraph.text
                    index += 1
        # return in_hymn_section and index also, because they can have a different start-value
        # based on whether there is a tile yes or no
        return in_hymn_section, index, title

    def get_hymn_image(self, hymn_data, paragraph):
        for run in paragraph.runs:
            for drawing in run._element.xpath('.//w:drawing'):
                for inline in drawing.xpath('.//wp:inline'):
                    for graphic in inline.xpath('.//a:graphic'):
                        for graphicData in graphic.xpath('.//a:graphicData'):
                            for pic in graphicData.xpath('.//pic:pic'):
                                for blipfill in pic.xpath('.//pic:blipFill'):
                                    for blip in blipfill.xpath('.//a:blip'):
                                        embed = blip.get(
                                            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                        if embed:
                                            image_part = self.word_document.part.related_parts[embed]
                                            image_bytes = image_part.blob
                                            hymn_data.append({"text": None, "images": [image_bytes]})

    def extract_paragraph_content(self, paragraph):
        paragraph_data = {"text": paragraph.text, "images": []}
        for run in paragraph.runs:
            for drawing in run._element.xpath('.//w:drawing'):
                for inline in drawing.xpath('.//wp:inline'):
                    for graphic in inline.xpath('.//a:graphic'):
                        for graphicData in graphic.xpath('.//a:graphicData'):
                            for pic in graphicData.xpath('.//pic:pic'):
                                for blipfill in pic.xpath('.//pic:blipFill'):
                                    for blip in blipfill.xpath('.//a:blip'):
                                        embed = blip.get(
                                            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                        if embed:
                                            image_part = self.word_document.part.related_parts[embed]
                                            image_bytes = image_part.blob
                                            paragraph_data["images"].append(image_bytes)
        return paragraph_data

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
                title_placeholder.text_frame.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) # White
                title_placeholder.text_frame.paragraphs[0].font.size = Pt(15)
                is_first_slide = False
            # add content (only image or text)
            if len(hymn["images"]) > 0:
                # Image formatting
                image_width = Inches(4)
                image_height = Inches(3)
                image_left = Inches(1)  # Fixed left offset
                image_top = Inches(1) # Fixed top offset
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
                            paragraph.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) # White
                            paragraph.font.size = Pt(12)
                        # set the text at the top:
                        p.text_frame.vertical_anchor = MSO_ANCHOR.TOP
                        last_bottom = 0
                    i = i + 1

    def calculate_text_height(self, text, font_size):
        """
        Calculates an approximate height for a given text block and font size.
        """
        lines = text.count('\n') + 1  # Count lines based on newline characters
        line_height = font_size * 1.2  # Approximate line height
        total_height_inches = (lines * line_height) / 72  # Convert points to inches
        return Inches(total_height_inches)

    def extract_collection_section(self, paragraphs):
        """
        Extracts the collection section (text and images) from a list of paragraphs.
        (Currently not implemented, just a placeholder.)

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data.
        """
        # Implementation for collection section to be added later
        return []

    def extract_intro_section(self, paragraphs):
        """
        Extracts the intro section (text and images) from a list of paragraphs.
        (Currently not implemented, just a placeholder.)

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data.
        """
        return []

    def extract_reading_section(self, paragraphs):
        """
        Extracts the reading section from a list of paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (title, reading_data)
                   title (str or None): The title of the reading section (or None if no title).
                   reading_data (list): A list of dictionaries, where each dictionary
                                        represents a part of the reading and contains
                                        its text (and potentially images, though they're not expected here).
        """
        print("extract_reading_section")
        reading_data = []
        current_text = []
        title = None
        new_index = 0
        in_reading_section = False
        index = -1
        # check if the reading-section has a title:
        if len(paragraphs) > 0:
            in_reading_section, index, title = self.get_reading_title(index, paragraphs)
        while self.current_paragraph_index + index < self.num_paragraphs-1:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]

            if self.tags["reading"]["begin"] in paragraph.text:
                # a new reading is started
                in_reading_section = True
                continue
            if self.check_end_tag("reading", paragraph):
                # no reading, but a next reading can be possible
                in_reading_section = False
                new_index = index + 1
                break
            if len(paragraph.text.strip()) == 0 and not in_reading_section:
                # empty line; skip
                new_index = index
                continue
            if len(paragraph.text.strip()) > 0 and not in_reading_section:
                # not next reading, so the reading-section is finished
                new_index = index
                break
            if in_reading_section:
                if len(paragraph.text) > 0:
                    cleaned_line = re.sub(r' {5,}', '\n', paragraph.text.strip())
                    current_text.append(cleaned_line)
        # Split the text into multiple parts if needed
        full_text = "\n".join(current_text)
        lines = full_text.split('\n')

        if len(lines) > self.max_reading_lines:
            parts = [lines[i:i + self.max_reading_lines] for i in range(0, len(lines), self.max_reading_lines)]
            for part in parts:
                reading_data.append({"text": "\n".join(part), "images": []})
        else:
            reading_data.append({"text": full_text, "images": []})
        self.current_paragraph_index = self.current_paragraph_index + new_index
        return title, reading_data

    def get_reading_title(self, index, paragraphs):
        title = None
        in_reading_section = False
        first_paragraph = paragraphs[0]
        # check if the first paragraph contains a title:
        if first_paragraph.runs and first_paragraph.runs[0].bold:
            title = first_paragraph.text
            if self.tags["reading"]["begin"] in title:
                title = title.replace(self.tags["reading"]["begin"], "")
                in_reading_section = True
            # check if this is a two-line title
            if len(paragraphs) > 1:
                second_paragraph = paragraphs[1]
                # check if the second paragraph is also part of the title.
                if second_paragraph.runs and second_paragraph.runs[0].bold:
                    title = title + "\n" + second_paragraph.text.strip()
                    index += 1
        # return in_reading_section and index also, because they can have a different start-value
        # based on whether there is a tile yes or no
        return in_reading_section, index, title

    def extract_organ_section(self, paragraphs):
        """
        Extracts the organ section (text and images) from a list of paragraphs.
        (Currently not implemented, just a placeholder.)

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data.
        """
        return []


    def extract_outro_section(self, paragraphs):
        """
        Extracts the outro section (text and images) from a list of paragraphs.
        (Currently not implemented, just a placeholder.)

        Args
        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data.
        """
        return []

# Main execution
if __name__ == "__main__":
    word_filename = "orde-van-dienst.docx"
    sermon = Sermon(word_filename)
    sermon.process_sermon()
