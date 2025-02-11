# sermon_extract.py
import re
from datetime import datetime

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
        title = None
        index = -1
        print("check for hymn sections")

        # check if the hymn-section has a title:
        if len(paragraphs) > 0:
            in_hymn_section, index, title = self.get_hymn_title(index, paragraphs)
        outro_data = {
            "image": None
        }
        def add_image_function(image, outro_data):
            outro_data["image"] = image

        def add_line_function(paragraph, current_text, _):
            current_text.append(paragraph.text)

        text = self._extract_section_text("hymn", add_image_function=add_image_function,
                                   add_line_function=add_line_function, outro_data=outro_data).strip()
        if outro_data["image"]:
            paragraph_data = {"text": "", "images": [outro_data["image"]]}
            hymn_data.append(paragraph_data)

        text = self.remove_title_from_text(text, title)

        split_list = self.split_string_list(text.split("\n"))
        for hymn in split_list:
            if len(hymn) == 0:
                continue
            paragraph_data = {"text": "\n".join(hymn), "images": []}
            hymn_data.append(paragraph_data)

        return title, hymn_data

    def remove_title_from_text(self, text, title):
        """
            Removes the first line of text if it starts with the title.

            Args:
                text (str): The text to potentially modify.
                title (str): The title to check against.

            Returns:
                str: The modified text, or the original text if it didn't start with the title.
            """
        # workaround because the title of the reading sometimes is repeated as the first line of the content
        title = title.strip()
        text = text.strip()
        text_lines = text.split("\n")
        title_lines = title.split("\n")
        # check if text_lines start with title_lines
        # if so: remove title_lines from text_lines
        if len(title_lines) > 0 and len(text_lines) >= len(title_lines):
            if text_lines[:len(title_lines)] == title_lines:
                text_lines = text_lines[len(title_lines):]

        text = "\n".join(text_lines)

        if text.startswith(title):
            # Find the first newline character
            first_newline_index = text.find('\n')

            if first_newline_index != -1:
                # Remove the first line (including the newline)
                text = text[first_newline_index + 1:]
            else:
                text = text[len(title):]
        return text

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
        def add_line_function(paragraph, current_text, _):
            cleaned_line = re.sub(r' {5,}', '\n', paragraph.text.strip())

            current_text.append(cleaned_line)
        full_text = self. _extract_section_text("offering", add_line_function = add_line_function)
        offering_goal, bank_account_number = self.extract_bank_account_number(full_text)
        offering_data = {"offering_goal": offering_goal, "bank_account_number": bank_account_number}
        return offering_data

    def _extract_section_text(self, section_name, add_line_function=None, outro_data=None, add_image_function=None):
        """
        Extracts text content from a specified section within the Word document.

        This method identifies the start and end of a named section within the
        Word document based on predefined tags and processes each paragraph
        within that section. It supports optional functions for processing each line of
        text and for handling images found within paragraphs.

        Args:
            section_name (str): The name of the section to extract text from (e.g., "offering").
                                 This name should correspond to a key in the `self.tags` dictionary,
                                 which contains the "begin" and "end" tags for the section.
            add_line_function (callable, optional): A function that processes each line of text
                                                     within the section. It takes three arguments:
                                                     - paragraph (docx.text.paragraph.Paragraph): The current paragraph object.
                                                     - current_text (list): The accumulating list of text lines.
                                                     - outro_data: Additional data passed from the caller.
                                                     Defaults to None. If None, no processing is done on the line.
            outro_data: Additional data passed to add_line_function.
            add_image_function (callable, optional): A function that processes an image when found in a
                                                      paragraph within the section. It takes two arguments:
                                                      - image_data: The data of the image.
                                                      - outro_data: Additional data passed from the caller.
                                                      Defaults to None. If None, no image processing is done.

        Returns:
            str: A string containing all the extracted text from the section, with each line separated by a newline character (`\n`).
                 Returns an empty string if the section is not found or contains no text.

        Raises:
            ValueError: If the `section_name` is not a valid key in `self.tags`.

        Attributes:
            self.word_document (docx.document.Document): The Word document object.
            self.current_paragraph_index (int): The index of the current paragraph being processed in the document.
            self.num_paragraphs (int): The total number of paragraphs in the document.
            self.tags (dict): A dictionary containing start and end tags for each section. Each key is a section name,
                              and each value is another dict containing "begin" and "end" keys with their respective tag strings.
        """
        if section_name not in self.tags:
            raise ValueError(f"The section_name should be one of {self.tags.keys()}, but is {section_name}")
        current_text = []  # Accumulator for lines of text in the section
        in_section = False  # Flag to indicate if the current paragraph is inside the section
        new_index = 0  # Keeps track of how many paragraphs have been read within the section
        index = -1  # Used to look ahead through paragraphs (starts at -1 because it increments before first use)

        # Iterate through paragraphs until the end of the document is reached
        while self.current_paragraph_index + index < self.num_paragraphs - 1:
            index += 1
            # Get the current paragraph to process
            paragraph = self.word_document.paragraphs[self.current_paragraph_index + index]

            # Check if the current paragraph is the start of the section
            if self.tags[section_name]["begin"] in paragraph.text:
                in_section = True  # Start of the section found
                # get the text after the section-tag
                t = paragraph.text.split(self.tags[section_name]["begin"])[-1]
                if t and add_line_function:
                    # remove the tag from the text
                    paragraph.text = t
                    # Process the part of the text after the tag
                    add_line_function(paragraph, current_text, outro_data)
                continue  # Move to the next paragraph

            # Check if the current paragraph is the end of the section
            if self.check_end_tag(section_name, paragraph):
                in_section = False  # Section end tag found
                new_index = index
                break  # Exit loop

            # Check for empty lines outside of section
            if len(paragraph.text.strip()) == 0 and not in_section:
                new_index = index
                continue  # Skip empty line

            # Check for text outside the section (means the section ended)
            if len(paragraph.text.strip()) > 0 and not in_section:
                new_index = index
                break  # Section finished

            # Process the text within the section
            if in_section:
                if len(paragraph.text) > 0 and add_line_function:
                    # Process the line with the add_line_function
                    add_line_function(paragraph, current_text, outro_data)

                new_index = index
                if add_image_function and self.paragraph_content_contains_image(paragraph):
                    # Process images in the paragraph with the add_image_function
                    # Extract and process the image
                    add_image_function(self.extract_paragraph_content(paragraph)["images"][0], outro_data)

        # Join the lines together into a single text string separated by newlines
        current_text = "\n".join(current_text)

        # Update the current paragraph index to after the end of the section
        self.current_paragraph_index = self.current_paragraph_index + new_index

        return current_text

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

        def add_line_function(paragraph, current_text, _):
            current_text.append(paragraph.text.strip())
        intro_text = self. _extract_section_text("intro", add_line_function = add_line_function)

        sermon = self.settings.get_setting('word-intro-date_label')
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
        parson_text = self.settings.get_setting("word-intro-parson_text")
        parson_match = re.search(rf"{parson_text}\s*\n\s*(.+)", intro_text)
        if parson_match:
            intro_data["parson"] = parson_match.group(1).strip()

        # Regex to find "Thema:" and capture the text on the following line(s)
        theme_text = self.settings.get_setting("word-intro-theme_text")
        theme_match = re.search(rf"{theme_text}\s*“([^“”]+)”", intro_text)
        if theme_match:
            theme = theme_match.group(1).strip()
            intro_data["theme"] = theme

        # Extract organ-player and performed piece
        organ_text = self.settings.get_setting("word-intro-organplayer_text")
        organist_match = re.search(rf"{organ_text}\s+(.+):\s+(.+)", intro_text)
        if organist_match:
            intro_data["organist"] = organist_match.group(1).strip()
            intro_data["performed_piece"] = organist_match.group(2).strip()

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
        title = None
        index = -1
        # check if the reading-section has a title:
        if len(paragraphs) > 0:
            in_reading_section, index, title = self.get_reading_title(index, paragraphs)
            # self.current_paragraph_index += index - 1

        def add_line_function(paragraph, current_text, _):
            cleaned_line = re.sub(r' {5,}', '\n', paragraph.text.strip())
            current_text.append(cleaned_line)
        full_text = self. _extract_section_text("reading", add_line_function = add_line_function).strip()
        # workaround because the title of the reading sometimes is repeated as the first line of the content
        full_text = self.remove_title_from_text(full_text, title).strip()

        parts = self.split_text_for_powerpoint(full_text)
        for part in parts:
            reading_data.append({"text": part})

        return title, reading_data

    def split_text_for_powerpoint(self, text, max_line_length=50, max_lines=14):
        """Splits a long text string into chunks that fit into PowerPoint text boxes.

        Args:
            text (str): The long text string to split.
            max_line_length (int, optional): The maximum number of characters per line. Defaults to 55.
            max_lines (int, optional): The maximum number of lines per text box. Defaults to 15.

        Returns:
            list: A list of strings, where each string is a text chunk that fits in a PowerPoint text box.
        """
        text_chunks = []
        lines = text.split('\n')  # Split the entire text into individual lines
        current_chunk_lines = []  # Lines for the current chunk

        for line in lines:
            # If adding the current line would exceed the max lines, split the chunk
            if len(current_chunk_lines) == max_lines:
                text_chunks.append('\n'.join(current_chunk_lines))
                current_chunk_lines = []  # Start a new chunk

            # Split the line if it exceeds the max line length
            while len(line) > max_line_length:
                split_index = line.rfind(' ', 0, max_line_length + 1)  # Find last space within limit
                if split_index == -1:
                    split_index = max_line_length  # Force split at limit if no space found
                current_chunk_lines.append(line[:split_index])
                line = line[split_index:].lstrip()  # Remove leading space from remainder

                # If adding the current line would exceed the max lines, split the chunk
                if len(current_chunk_lines) == max_lines:
                    text_chunks.append('\n'.join(current_chunk_lines))
                    current_chunk_lines = []  # Start a new chunk

            current_chunk_lines.append(line)  # Add the remaining part of the line

        # Split at the last newline of the last chunk, if possible
        if current_chunk_lines:
            last_chunk = '\n'.join(current_chunk_lines)
            last_newline_index = last_chunk.rfind('\n')

            if last_newline_index != -1 and len(current_chunk_lines)==max_lines:
                text_chunks.append(last_chunk[:last_newline_index])
                text_chunks.append(last_chunk[last_newline_index + 1:])
            else:
                text_chunks.append(last_chunk)

        return text_chunks

    def extract_illustration(self, paragraphs):
        """
        Extracts the illustration from the given paragraphs.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (image_data, image_content_type) or (None, None) if no illustration is found.
        """
        print("extract_illustration")

        outro_data = {
            "image": None
        }
        def add_image_function(image, outro_data):
            outro_data["image"] = image

        self._extract_section_text("illustration", add_image_function=add_image_function, outro_data=outro_data)
        return outro_data["image"]


    def extract_outro_section(self, paragraphs):
        """
        Extracts the date and parson from the outro section.

        Args:
            paragraphs (list): A list of paragraphs (docx.paragraph.Paragraph objects).

        Returns:
            tuple: (date, parson) or (None, None) if not found.
        """
        print("extract_outro_section")
        current_text = []

        # Use a dictionary to store the values, that will be used as the closure for the function add_line_function
        outro_data = {
            "date_text": "",
            "parson": "",
            "performed_piece": "",
            "previous_line_is_sermon": False,
            "organ_text": self.settings.get_setting("word-outro-organ_text"),
            "next_sermon_text": self.settings.get_setting("word-outro-next_sermon_text")
        }

        # define the function, that will use the closure that is defined in the lines above
        def add_line_function(paragraph, _, outro_data):
            if outro_data["organ_text"] in paragraph.text:
                organ_text = outro_data["organ_text"]
                performed_piece_match = re.search(rf"{organ_text}\s*(.+)", paragraph.text.strip()) # use f-string
                if performed_piece_match:
                    outro_data["performed_piece"] = performed_piece_match.group(1).strip()
            if outro_data["next_sermon_text"].lower() in paragraph.text.lower():
                outro_data["previous_line_is_sermon"] = True
                return

            if outro_data["previous_line_is_sermon"]:
                parts = paragraph.text.split('\t')
                outro_data["previous_line_is_sermon"] = False
                if len(parts) >= 2:
                    date_text1 = parts[0]
                    parson1 = parts[len(parts) - 1]
                    date_text1 = self.format_date(date_text1)
                    outro_data["date_text"] = date_text1
                    outro_data["parson"] = parson1
        self._extract_section_text("outro", add_line_function = add_line_function, outro_data = outro_data)
        #make sure the program will end here
        self.current_paragraph_index = 200000

        return outro_data["date_text"], outro_data["parson"], outro_data["performed_piece"]

    def extract_bank_account_number(self, text):
        """
        Extracts the offering goal and bank account number from the text.

        Args:
            text (str): The text from the offering section.

        Returns:
            tuple: (offering_goal, bank_account_number)
        """
        bank_account_number = ""
        offering_goal = ""
        # Split the text at the "blauwe zak"
        blue_bag_text = self.settings.get_setting("word-offering-blue_bag_text")
        parts = text.split(blue_bag_text)
        first_part_of_offering_text = parts[0]

        # Regex to find the bank account number (IBAN) in the first part
        bank_account_regex = "([A-Z]{2}\d{2}\s[A-Z]{4}\s\d{4}\s\d{4}\s\d{2})"
        bank_number_match = re.search(bank_account_regex, first_part_of_offering_text)
        if bank_number_match:
            bank_account_number = bank_number_match.group(1).strip()

        # Clean the bank account number
        bank_account_number = re.sub(r"[^a-zA-Z0-9]", " ", bank_account_number)  # Replace non-alphanumeric with space
        bank_account_number = re.sub(r"\s{2,}", " ", bank_account_number)  # Replace multiple spaces with one
        bank_account_number = bank_account_number.strip()

        # Regex to find offering goal (text after "1ste (rode zak) Diaconie:")
        red_bag_text = self.settings.get_setting("word-offering-red_bag_text")
        diaconie_text = self.settings.get_setting("word-offering-diaconie_text")

        offering_goal_regex = fr"1ste \({red_bag_text}\)\s*{diaconie_text}\s*(.*?)(?=\n|$)"
        goal_match = re.search(offering_goal_regex, text)
        if goal_match:
            offering_goal = goal_match.group(1).strip()
        return offering_goal, bank_account_number


