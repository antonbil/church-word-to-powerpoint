from docx import Document
from docx.shared import Pt, Inches
from pptx import Presentation
from pptx.util import Inches
import os
import io
import re
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

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
        self.powerpoint_filename = os.path.splitext(word_filename)[0] + ".pptx"
        self.word_document = None
        self.powerpoint_presentation = None
        # current_paragraph_index is the pointer to the current paragraph in the Word-file
        self.current_paragraph_index = 0
        self.num_paragraphs = 0
        # Define the tags
        self.tags = {
            "hymn": {"begin": "[Li]", "end": "[/Li]"},
            "collection": {"begin": "begin-collecte-tag", "end": "eind-collecte-tag"},
            "intro": {"begin": "begin-intro-tag", "end": "eind-intro-tag"},
            "reading": {"begin": "begin-lezing-tag", "end": "eind-lezing-tag"},
            "organ": {"begin": "begin-orgelspel-tag", "end": "eind-orgelspel-tag"},
            "outro": {"begin": "begin-outro-tag", "end": "eind-outro-tag"}
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
            self.powerpoint_presentation = Presentation()
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
                        hymn_data = self.extract_hymn_section(paragraphs[self.current_paragraph_index:])
                        self.create_hymn_slides(hymn_data)
                    elif self.current_tag == "collection":
                        collection_data = self.extract_collection_section(paragraphs[self.current_paragraph_index:])
                        # self.create_collection_slides(collection_data)
                    elif self.current_tag == "intro":
                        intro_data = self.extract_intro_section(paragraphs[self.current_paragraph_index:])
                        # self.create_intro_slides(intro_data)
                    elif self.current_tag == "reading":
                        reading_data = self.extract_reading_section(paragraphs[self.current_paragraph_index:])
                        # self.create_reading_slides(reading_data)
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
        Extracts the hymn sections (text and images) from a list of paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data
        """
        hymn_data = []
        new_index = 0
        in_hymn_section = False
        index = -1
        print("check for hymn sections")
        print(self.current_paragraph_index)
        while self.current_paragraph_index < self.num_paragraphs:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]
            #print(paragraph.text)
            if self.tags["hymn"]["begin"] in paragraph.text:
                # a new hymn is started
                in_hymn_section = True
                continue
            if self.tags["hymn"]["end"] in paragraph.text:
                # no hymn, but a next hymn can be possible
                in_hymn_section = False
                new_index = index + 1
                continue
            if len(paragraph.text.strip()) > 0 and not in_hymn_section:
                # not next hymn, so the hymn-section is finished
                new_index = index
                break
            if in_hymn_section:
                paragraph_data = {"text": paragraph.text, "images": []}
                for run in paragraph.runs:
                    for drawing in run._element.xpath('.//w:drawing'):
                        for inline in drawing.xpath('.//wp:inline'):
                            for graphic in inline.xpath('.//a:graphic'):
                                for graphicData in graphic.xpath('.//a:graphicData'):
                                    for pic in graphicData.xpath('.//pic:pic'):
                                        for blipfill in pic.xpath('.//pic:blipFill'):
                                            for blip in blipfill.xpath('.//a:blip'):
                                                embed = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                                if embed:
                                                    image_part = self.word_document.part.related_parts[embed]
                                                    image_bytes = image_part.blob
                                                    paragraph_data["images"].append(image_bytes)
                print(paragraph.text)
                hymn_data.append(paragraph_data)
        self.current_paragraph_index = self.current_paragraph_index + new_index
        return hymn_data

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
        Extracts the reading section (text and images) from a list of paragraphs.
        (Currently not implemented, just a placeholder.)

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  paragraph and contains its text and image data.
        """
        return []

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

    def create_hymn_slides(self, hymn_data):
        """
        Creates PowerPoint slides for the hymn sections.

        Args:
            hymn_data: A list of dictionaries containing hymn data (text and images).
        """
        print("add hymn-data")
        if not self.powerpoint_presentation:
            print("Error: PowerPoint presentation not initialized.")
            return

        # add a blank slide
        blank_slide_layout = self.powerpoint_presentation.slide_layouts[6]
        slide = self.powerpoint_presentation.slides.add_slide(blank_slide_layout)
        text = []
        for paragraph_data in hymn_data:
            text.append(paragraph_data["text"])
            if len(paragraph_data["images"]) > 0:
                image_bytes = paragraph_data["images"][0]
                image_stream = io.BytesIO(image_bytes)
                slide.shapes.add_picture(image_stream, left=Inches(1), top=Inches(3), width=Inches(6))

        left = top = width = height = Inches(1)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.text = "\n".join(text)

        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        p.font.bold = False
        p.font.size = Pt(24)

# Main execution
if __name__ == "__main__":
    word_filename = "orde-van-dienst.docx"
    sermon = Sermon(word_filename)
    sermon.process_sermon()
