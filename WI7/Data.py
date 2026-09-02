

'''
data.py

Author: Trinh Pham

This script is for the class Data. It will abstract the image file and text files for flexibility.

Subclasses: c_ImageData, c_TextData
Each subclass will store an array of its respective data type.
'''

class c_Data: # Base class for different types of data (image, text, etc.)

    def __init__(self, fpFilePath: str) -> None:
        self.fpFilePath = fpFilePath
        self.data = []

    def f_get_file_path(self) -> str:  # gets the file path associated with the data
        return self.fpFilePath

class c_ImageData(c_Data): # MongoDB can use BSON or GridFS (recommended) for storing images in its DB

    def __init__(self, fpFilePath: str) -> None:
        super().__init__(fpFilePath)

    def f_add_image(self, pImage) -> None:  # adds an image to the data list
        self.data.append(pImage)

    def f_get_images(self) -> list:  # gets array of images itself, not file path
        return self.data

    

class c_TextData(c_Data): # Text data can be stored as plain text in MongoDB
    def __init__(self, fpFilePath: str) -> None:
        super().__init__(fpFilePath)

    def f_add_text(self, acText: str) -> None:  # adds a text entry to the data list
        self.data.append(acText)

    def f_get_texts(self) -> list:  # gets array of texts itself, not file path
        return self.data