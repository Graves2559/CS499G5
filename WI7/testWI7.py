import tempfile
import unittest
from pathlib import Path

from WI7.Data import c_ImageData, c_TextData
from WI7.Import import c_ImportData
from WI7.main import f_dataObjectConvert

# Will test each function to ensure correct behavior - unit tests


# Unit tests for the Data classes
class c_DataTests(unittest.TestCase):

    # verifies that the text data stores and retrieves texts correctly
    def test_text_data_stores_text(self):
        pData = c_TextData("example.txt")

        pData.f_add_text("Hello")

        self.assertEqual(pData.f_get_file_path(), "example.txt")
        self.assertEqual(pData.f_get_texts(), ["Hello"])

    # verifies that the image data stores and retrieves images correctly
    def test_image_data_stores_image(self):
        pData = c_ImageData("example.png")
        pImage = object()

        pData.f_add_image(pImage)

        self.assertEqual(pData.f_get_images(), [pImage])


# Unit tests for the ImportData Class
class c_ImportDataTests(unittest.TestCase):
    # parses text data from a JSON lines file
    def test_parse_text_data_reads_json_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as file:
            file.write('{"name": "Alice"}\n{"name": "Bob"}\n')
            fpFilePath = file.name

        self.addCleanup(Path(fpFilePath).unlink)
        pImporter = c_ImportData(c_TextData(fpFilePath))

        pImporter.f_parse()

        self.assertEqual(pImporter.f_get_data(), [{"name": "Alice"}, {"name": "Bob"}])

    # ensures that invalid JSON lines result in an empty data list
    def test_parse_text_data_returns_empty_list_for_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as file:
            file.write("not valid JSON\n")
            fpFilePath = file.name

        self.addCleanup(Path(fpFilePath).unlink)
        pImporter = c_ImportData(c_TextData(fpFilePath))

        pImporter.f_parse()

        self.assertEqual(pImporter.f_get_data(), [])

    # parses image data from a JSON lines file
    def test_image_data_parses_json_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".png", delete=False) as file:
            file.write("fake image data")
            fpFilePath = file.name

        self.addCleanup(Path(fpFilePath).unlink)
        pImporter = c_ImportData(c_ImageData(fpFilePath))

        pImporter.f_parse()

        self.assertEqual(pImporter.f_get_data(), ["fake image data"])

    # Verifies that an incorrect format for either text is handled appropriately
    def test_parse_incorrect_format_returns_empty_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as file:
            file.write("not valid JSON\n")
            fpFilePath = file.name

        self.addCleanup(Path(fpFilePath).unlink)
        pImporter = c_ImportData(c_TextData(fpFilePath))

        pImporter.f_parse()

        self.assertEqual(pImporter.f_get_data(), [])

    # Verifies that an incorrect format for image data is handled appropriately
    def test_parse_incorrect_image_format_returns_empty_list(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".png", delete=False) as file:
            file.write("not valid image data\n")
            fpFilePath = file.name

        self.addCleanup(Path(fpFilePath).unlink)
        pImporter = c_ImportData(c_ImageData(fpFilePath))

        pImporter.f_parse()

        self.assertEqual(pImporter.f_get_data(), [])


class c_ConversionTests(unittest.TestCase):
    # verifies that the data object conversion selects the correct type based on file extension
    def test_data_object_convert_selects_type_from_extension(self):
        self.assertIsInstance(f_dataObjectConvert(Path("notes.txt")), c_TextData)
        self.assertIsInstance(f_dataObjectConvert(Path("photo.png")), c_ImageData)

    # ensures that unknown file extensions raise a ValueError
    def test_data_object_convert_rejects_unknown_extension(self):
        with self.assertRaises(ValueError):
            f_dataObjectConvert(Path("archive.pdf"))


if __name__ == "__main__":
    unittest.main()