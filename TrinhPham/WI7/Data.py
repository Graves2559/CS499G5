

'''
data.py

Author: Trinh Pham

This script is for the class Data. It will abstract the image file and text files for flexibility.

Subclasses: ImageData, TextData
Each subclass will store an array of its respective data type.
'''

class Data: # Base class for different types of data (image, text, etc.)

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.data = []

    def f_get_file_path(self) -> str:
        return self.file_path

class ImageData(Data): # MongoDB can use BSON or GridFS (recommended) for storing images in its DB

    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def f_add_image(self, image) -> None:
        self.data.append(image)

    def f_get_images(self) -> list:
        return self.data

    

class TextData(Data): # Text data can be stored as plain text in MongoDB
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def f_add_text(self, text) -> None:
        self.data.append(text)

    def f_get_texts(self) -> list:
        return self.data