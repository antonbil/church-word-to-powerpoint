# Church Service PPT Creator

This project automates the process of creating PowerPoint presentations for church services from a Word document. It extracts relevant information from the Word document, such as the date, time, parson, theme, organist, songs, and scripture readings, and then uses that information to create visually appealing slides in a PowerPoint presentation.

## Features

* **Word Document Parsing:** Extracts information from a specifically formatted Word document.

* **PowerPoint Generation:** Automatically generates a PowerPoint presentation with title slides and content slides.

* **Customizable:** The style of the generated PowerPoint can be customized via settings.json.

* **Data Extraction:** Extracts essential data from the Word document, including:

  * Date and time of the service.

  * Name of the parson.

  * Service theme.

  * Name of the organist.

  * List of songs.

  * List of scripture readings.

  * Outro text.

* **Day of the week**: The day of the week is added to the date.

* **Themes**: you can add multiple themes to the generated powerpoint.

## Prerequisites

* Python 3.x

* The following Python libraries:

  * python-docx

  * python-pptx

  * python-slugify

## Installation

1. Clone this repository:
   bash git clone \[repository-url\]

2. Install the required Python libraries:
   bash pip install python-docx python-pptx python-slugify

## Usage

1. Prepare your Word document with the following layout:

   * The `intro section` start with: `%intro begin%` and ends with `%intro end%`

     * the date is in the following format: `5 januari 2025`.

     * the time is in the following format: `10.00 uur`.

     * The theme is after the word: `Thema:`.

     * The parson is after the word: `Voorganger:`.

     * The organist is after the words: `Orgelspel ... door`.

   * The `songs` start with: `%songs begin%` and ends with `%songs end%`

     * The text contains the songs in the following format:

     * `Song 1: Psalm 123, vers 1 en 2.`

     * `Song 2: Gezang 456.`

     * `Song 3: Lied 789.`

   * The `readings` start with: `%readings begin%` and ends with `%readings end%`

     * The text contains the readings in the following format:

     * `Reading 1: Genesis 1.`

     * `Reading 2: Romeinen 2, vers 1-5.`

   * The `outro` start with: `%outro begin%` and ends with `%outro end%`

     * The date is in the format: `2025-01-05`

   * The file must be a `.docx` file.

2. Adjust `settings.json` if needed.

   * The font-colors and background color can be changed.

   * The titles can be changed.

   * The output folder can be changed.

3. Run `main.py`:
   bash python3 -m Sermon.main

* This will generate the powerpoint `.pptx` file in the `output` folder.

## File Structure

KeizerChess/

├── Sermon/ │

├── init.py │

├── main.py │

├── sermon_create.py │

├── sermon_extract.py │

└── settings.json

├── my_presentation.pptx #the test-presentation file

├── README.md #this file

└── input/

└── input_file.docx #the input file

## Contributing

Feel free to contribute to this project by opening issues or pull requests.

## Acknowledgements

This project was created with the support and guidance of:
Gemini, an AI assistant, for code generation and problem-solving assistance.

## Contact

Author: Anton Bil
Email: anton.bil.167@gmail.com

## License

This project is licensed under the MIT License.
