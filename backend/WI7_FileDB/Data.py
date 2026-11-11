

'''
data.py

Author: Trinh Pham

This script is for the class Data. It will abstract the image file and text files for flexibility.

Subclasses: c_ImageData, c_TextData
Each subclass will store an array of its respective data type.
'''

import mimetypes
from pathlib import Path

class c_Data: # Base class for different types of data (image, text, etc.)

    def __init__(self, fpFilePath: str) -> None:
        self.fpFilePath = fpFilePath

        # Determine the content (or MIME) type of the file, defaulting to binary if unknown
        self.type = mimetypes.guess_type(fpFilePath)[0] or "application/octet-stream"
            # Mime types: Text, Image, Video, Audio, Application, etc. or unknown binary (the octet stream)

        self.data = []

    def f_get_file_path(self) -> str:  # gets the file path associated with the data
        return self.fpFilePath

    def f_get_data(self) -> list:  # gets the array of data itself, not file path
        return self.data

    def f_add_data(self, pData) -> None:  # adds a generic data entry to the data list
        self.data.append(pData)

    def f_get_content_type(self) -> str:  # gets the MIME (content) type of the file
        return self.type

    # Use file path to get MIME (content) type of the file, then instantiate the appropriate subclass based on the content type.    
    def f_convert_to_data_class(self):
        fpFilePath = Path(self.fpFilePath)

        # Instantiate the appropriate subclass based on the content type.
        if self.type.startswith("text/"): self = c_TextData(fpFilePath)
        elif self.type.startswith("image/"): self = c_ImageData(fpFilePath)
        elif self.type.startswith("video/"): self = c_VideoData(fpFilePath)
        else: self = c_Data(fpFilePath)
        return self


# Later: add captions embedded into this file
class c_ImageData(c_Data): # MongoDB can use BSON or GridFS (recommended) for storing images in its DB

    def __init__(self, fpFilePath: str) -> None:
        super().__init__(fpFilePath)


class c_TextData(c_Data): # Text data can be stored as plain text in MongoDB
    def __init__(self, fpFilePath: str) -> None:
        super().__init__(fpFilePath)

# Later: add captions embedded into this file
class c_VideoData(c_Data): # Video data can be stored as binary in MongoDB (BSON or GridFS)

    def __init__(self, fpFilePath: str) -> None:
        super().__init__(fpFilePath)

