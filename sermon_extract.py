# sermon_extract.py
from docx import Document
import re
class SermonExtract:
    """
    Contains the methods for extracting information from the Word document.
    """

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
        Extracts the date and parson from the outro section.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (date, parson) or (None, None) if not found.
        """
        print("extract_outro_section")
        new_index = 0
        index = -1
        in_outro_section = False
        for paragraph in paragraphs:
            print(paragraph.text)
            index = index + 1
            if self.tags["outro"]["begin"] in paragraph.text:
                # a new outro is started
                in_outro_section = True
                continue
            if self.check_end_tag("outro", paragraph):
                # no outro, but a next outro can be possible
                in_outro_section = False
                new_index = index + 1
                break
            if len(paragraph.text.strip()) == 0 and not in_outro_section:
                # empty line; skip
                new_index = index
                continue
            if len(paragraph.text.strip()) > 0 and not in_outro_section:
                # not next outro, so the outro-section is finished
                new_index = index
                break
            if "Volgende vieringen/activiteiten:".lower() in paragraph.text.lower():
                next_paragraph = paragraphs[index + 1]

                parts = next_paragraph.text.split('\t')
                print("parts")
                print(parts)
                if len(parts) >= 2:
                    date_text = parts[0]
                    parson = parts[len(parts) - 1]
                    date_text = self.format_date(date_text)
                    new_index = index
                    self.current_paragraph_index = self.current_paragraph_index + new_index
                    return date_text, parson

        self.current_paragraph_index = self.current_paragraph_index + new_index
        return None, None
