# sermon_utils.py
import datetime
from pptx.util import Inches

class SermonUtils:
    """
    Contains utility methods for the Sermon class.
    """

    def format_date(self, date_text):
        """
        Formats the date from "12-jan" to "Zondag 12 januari 2025".
        """
        try:
            date_obj = datetime.datetime.strptime(date_text, "%d-%b")
            date_obj = date_obj.replace(year=2025)
            day_of_week = self.get_day_of_week(date_obj.weekday())
            formatted_date = date_obj.strftime("%d %B %Y")
            return f"{day_of_week} {formatted_date}"
        except ValueError:
            return None

    def get_day_of_week(self, weekday_number):
        """
        Returns the Dutch day of the week name for a given weekday number (0-6).
        """
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        return days[weekday_number] if 0 <= weekday_number <= 6 else None

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
            title = title.strip()
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

    def calculate_text_height(self, text, font_size):
        """
        Calculates an approximate height for a given text block and font size.
        """
        lines = text.count('\n') + 1  # Count lines based on newline characters
        line_height = font_size * 1.2  # Approximate line height
        total_height_inches = (lines * line_height) / 72  # Convert points to inches
        return Inches(total_height_inches)
