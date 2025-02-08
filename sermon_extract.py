# sermon_extract.py
from docx import Document
import re
from datetime import datetime
import locale
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
        # print(self.current_paragraph_index)

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
                # print(paragraph.text)
                if len(paragraph.text) > 0:
                    current_text.append(paragraph.text)

                # check if the hymn-section starts with a picture:
                if len(hymn_data) == 0:
                    # if first paragraph in hymn-section contains an image, this is considered as a 'hymn'
                    self.get_hymn_image(hymn_data, paragraph)
        self.current_paragraph_index = self.current_paragraph_index + new_index
        return title, hymn_data

    def extract_offering_section(self, paragraphs):
        """
        Extracts the offering section (text) from a list of paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (offering_data)
                   offering_data (list): A list of dictionaries, where each dictionary
                                        represents a part of the offering and contains
                                        its text.
        """
        print("extract_offering_section")
        offering_data = []
        current_text = []
        new_index = 0
        in_offering_section = False
        index = -1
        while self.current_paragraph_index + index < self.num_paragraphs - 1:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]

            if self.tags["offering"]["begin"] in paragraph.text:
                # a new offering is started
                in_offering_section = True
                continue
            if self.check_end_tag("offering", paragraph):
                # no offering, but a next offering can be possible
                in_offering_section = False
                new_index = index + 1
                break
            if len(paragraph.text.strip()) == 0 and not in_offering_section:
                # empty line; skip
                new_index = index
                continue
            if len(paragraph.text.strip()) > 0 and not in_offering_section:
                # not next offering, so the offering-section is finished
                new_index = index
                break
            if in_offering_section:
                if len(paragraph.text) > 0:
                    cleaned_line = re.sub(r' {5,}', '\n', paragraph.text.strip())
                    current_text.append(cleaned_line)
        # Split the text into multiple parts if needed
        full_text = "\n".join(current_text)
        offering_goal, bank_account_number = self.extract_bank_account_number(full_text)
        offering_data = {"offering_goal": offering_goal, "bank_account_number": bank_account_number}
        self.current_paragraph_index = self.current_paragraph_index + new_index
        return offering_data


    def extract_bank_account_number(self, text):
        """
        Extracts the offering goal and bank account number from the text.

        Args:
            text (str): The text from the offering section.

        Returns:
            tuple: (offering_goal, bank_account_number)
        """
        print("extract_bank_account_number")
        bank_account_number = ""
        offering_goal = ""
        # Split the text at the "blauwe zak"
        blue_bag_text = self.settings.get_setting("offering_blue_bag_text")  # New
        parts = text.split(blue_bag_text)  # Modified
        first_part = parts[0]

        # Regex to find the bank account number (IBAN) in the first part
        bank_account_regex = "([A-Z]{2}\d{2}\s[A-Z]{4}\s\d{4}\s\d{4}\s\d{2})"
        bank_number_match = re.search(bank_account_regex, first_part)
        if bank_number_match:
            bank_account_number = bank_number_match.group(1).strip()

        # Clean the bank account number
        bank_account_number = re.sub(r"[^a-zA-Z0-9]", " ", bank_account_number)  # Replace non-alphanumeric with space
        bank_account_number = re.sub(r"\s{2,}", " ", bank_account_number)  # Replace multiple spaces with one
        bank_account_number = bank_account_number.strip()

        # Regex to find offering goal (text after "1ste (rode zak) Diaconie:")
        red_bag_text = self.settings.get_setting("offering_red_bag_text")
        diaconie_text = self.settings.get_setting("offering_diaconie_text")
        # the old regex: r"1ste \(rode zak\) Diaconie:\s*(.*?)(?=\n|$)"
        offering_goal_regex = fr"1ste \({red_bag_text}\)\s*{diaconie_text}\s*(.*?)(?=\n|$)"
        goal_match = re.search(offering_goal_regex, text)
        if goal_match:
            offering_goal = goal_match.group(1).strip()
        return offering_goal, bank_account_number

    def extract_intro_section(self, paragraphs):
        """
        Extracts the introduction section (date, time, parson, theme, organist) from a list of paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            dict: A dictionary containing the extracted information:
                  {
                      "date": "Zondag 5 januari 2025",
                      "time": "10.00 uur",
                      "parson": "ds. Elly van Kuijk-Spaans",
                      "theme": "“Zaaien: een gids voor beginners”",
                      "organist": "Martin van der Bent"
                  }
        """
        print("extract_intro_section")
        intro_data = {}
        current_text = []
        new_index = 0
        in_intro_section = False
        index = -1
        while self.current_paragraph_index + index < self.num_paragraphs - 1:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]

            if self.tags["intro"]["begin"] in paragraph.text:
                # a new intro is started
                in_intro_section = True
                continue
            if self.check_end_tag("intro", paragraph):
                # no intro, but a next intro can be possible
                in_intro_section = False
                new_index = index + 1
                break
            if len(paragraph.text.strip()) == 0 and not in_intro_section:
                # empty line; skip
                new_index = index
                continue
            if len(paragraph.text.strip()) > 0 and not in_intro_section:
                # not next intro, so the intro-section is finished
                new_index = index
                break
            if in_intro_section:
                if len(paragraph.text) > 0:
                    current_text.append(paragraph.text.strip())
        intro_text = "\n".join(current_text)
        sermon = self.settings.get_setting('intro_date_label')
        # Extract date
        sermon_date_list = [l for l in current_text if sermon in l]
        date_text = "25 december 2024"
        if len(sermon_date_list) > 0:
            l2 = sermon_date_list[0].split(sermon)
            if len(l2) > 1:
                date_text = l2[1].strip()

        # Convert month names to numbers
        month_numbers = {
            "januari": "1",
            "februari": "2",
            "maart": "3",
            "april": "4",
            "mei": "5",
            "juni": "6",
            "juli": "7",
            "augustus": "8",
            "september": "9",
            "oktober": "10",
            "november": "11",
            "december": "12",
        }

        intro_data["date"] = date_text
        if date_text:
            day, month_name, year = date_text.split()
            month_number = month_numbers.get(month_name.lower())
            if month_number:
                numeric_date_str = f"{day} {month_number} {year}"
                try:
                    date_object = datetime.strptime(numeric_date_str, "%d %m %Y")
                    intro_data["date"] = f"{self.get_day_of_week(date_object.weekday())} {date_text}"
                except ValueError as e:
                    print(f"Error parsing date: {e}")

        # Extract time
        time_match = re.search(r"(\d{1,2}\.\d{2}\suur)", intro_text)
        if time_match:
            intro_data["time"] = time_match.group(1)

        # Extract parson
        parson_match = re.search(r"Voorganger:\s*\n\s*(.+)", intro_text)
        if parson_match:
            intro_data["parson"] = parson_match.group(1).strip()

        # Extract theme
        theme_match = re.search(r"Thema:\s*\n\s*(.+)", intro_text)
        if theme_match:
            intro_data["theme"] = theme_match.group(1).strip()

        # Extract organist and performed piece
        organist_match = re.search(r"Orgelspel.*door\s+(.+):\s+(.+)", intro_text)
        if organist_match:
            intro_data["organist"] = organist_match.group(1).strip()
            intro_data["performed_piece"] = organist_match.group(2).strip()

        self.current_paragraph_index = self.current_paragraph_index + new_index
        # print(intro_data)
        return intro_data

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

    def extract_illustration(self, paragraphs):
        """
        Extracts the illustration from the given paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (image_data, image_content_type) or (None, None) if no illustration is found.
        """
        print("extract_illustration")

        in_illustration_section = False
        image = None
        index = -1
        illustration_data = []
        while self.current_paragraph_index + index < self.num_paragraphs-1:
            index = index + 1
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]
            if self.tags["illustration"]["begin"] in paragraph.text:
                in_illustration_section = True
                continue
            if self.check_end_tag("illustration", paragraph):
                in_illustration_section = False
                break
            if in_illustration_section:

                    self.extract_paragraph_content(paragraph)

                    # if first paragraph in hymn-section contains an image, this is considered as a 'hymn'
                    self.get_hymn_image(illustration_data, paragraph)

        self.current_paragraph_index = self.current_paragraph_index + index
        if len(illustration_data) > 0:
            image = illustration_data[0]["images"][0]
        return image

    def get_image(self, paragraph):
        image = None
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
                                            image = image_bytes
        return image


    # def get_image(self, paragraph):
    #     """
    #     Extracts the image data from the given paragraph.
    #
    #     Args:
    #         paragraph (docx.paragraph.Paragraph): The paragraph to extract the image from.
    #
    #     Returns:
    #         tuple: (image_data, image_content_type) or (None, None) if no image is found.
    #     """
    #     for inline_shape in paragraph.runs[0]._r.drawing_lst[0].inline_shapes:
    #         image_part = inline_shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    #         image_data = self.word_document.part.related_parts[image_part].blob
    #         image_content_type = self.word_document.part.related_parts[image_part].content_type
    #         return image_data, image_content_type
    #     return None, None

    def has_image(self, paragraph):
        """
        Checks if the paragraph has an image.

        Args:
            paragraph (docx.paragraph.Paragraph): The paragraph to check.

        Returns:
            bool: True if the paragraph has an image, False otherwise.
        """
        if paragraph.runs and paragraph.runs[0]._r.drawing_lst is not None:
            return True
        return False

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
        performed_piece = ""
        in_outro_section = False
        for paragraph in paragraphs:
            index = index + 1
            # add check for performed_piece_match first, befoe checking for the self.tags["outro"]["begin"]
            # otherwise the line is removed, and the correct title not set.
            if "Orgelspel:" in paragraph.text:
                performed_piece_match = re.search(r"Orgelspel:\s*(.+)", paragraph.text)
                if performed_piece_match:
                    performed_piece = performed_piece_match.group(1).strip()
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
                if len(parts) >= 2:
                    date_text = parts[0]
                    parson = parts[len(parts) - 1]
                    date_text = self.format_date(date_text)
                    new_index = index
                    self.current_paragraph_index = self.current_paragraph_index + new_index
                    return date_text, parson, performed_piece

        self.current_paragraph_index = self.current_paragraph_index + new_index
        return None, None
