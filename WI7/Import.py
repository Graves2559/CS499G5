
'''
import.py

Author: Trinh Pham

This script is a class for importing data into a MongoDB database. 

Inputs: Data.txt
'''

'''
Class for importing data into MongoDB.
Uses dependency injection for data.txt input. 
'''

import json
import logging
from PIL import Image

try:
    from . import Data
except ImportError:
    import Data


logger = logging.getLogger(__name__)


class c_ImportData:
    data: Data.c_Data # for using Data object to access its methods (getFilePath and getData)
    result: list[dict[str, object] | Image.Image]       # Image(module from PIL).Image(an Image Object from said Module)

    def __init__(self, pData: Data.c_Data) -> None:
        self.data = pData
        self.result = []

    def f_import_toMongo(self) -> None:
        # Code to import self.data into MongoDB goes here
        pass

    def f_parse(self) -> None:
        # Minimum guarantee: self.data must be a Data object before parsing
        if not isinstance(self.data, Data.c_Data):            # inverse guard clause
            logger.error("parse() requires a Data object")
            return

        fpFilePath = self.data.f_get_file_path()    # More writability for subsequent file operations

        if isinstance(self.data, Data.c_TextData):
            try:
                with open(fpFilePath, 'r') as file:
                    self.result = [json.loads(acLine) for acLine in file if acLine.strip()]
            except json.JSONDecodeError:
                self.result = []
                logger.exception("parse() failed to parse JSON")
        elif isinstance(self.data, Data.c_ImageData):
            pImage = Image.open(fpFilePath)
            self.data.f_add_image(pImage)
            self.result = self.data.f_get_images()
            pImage.show()
        else:
            logger.error("Unsupported data type for parsing")


    def f_connect_toMongo(self) -> bool:
        # Code to connect to MongoDB goes here
        return False

    def f_get_data(self) -> list[dict[str, object] | Image.Image]:
        return self.result


    