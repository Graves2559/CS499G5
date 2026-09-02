
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
import Data
from PIL import Image


logger = logging.getLogger(__name__)


class c_ImportData:
    data: Data.Data # for using Data object to access its methods (getFilePath and getData)
    result: list[dict[str, object] | Image.Image]

    def __init__(self, data: Data.Data) -> None:
        self.data = data
        self.result = []

    def f_import_toMongo(self) -> None:
        # Code to import self.data into MongoDB goes here
        pass

    def f_parse(self) -> None:
        # Minimum guarantee: self.data must be a Data object before parsing
        if not isinstance(self.data, Data.Data):            # inverse guard clause
            logger.error("parse() requires a Data object")
            return

        file_path = self.data.f_get_file_path()

        if isinstance(self.data, Data.TextData):
            try:
                with open(file_path, 'r') as file:
                    self.result = [json.loads(line) for line in file if line.strip()]
            except json.JSONDecodeError:
                self.result = []
                logger.exception("parse() failed to parse JSON")
        elif isinstance(self.data, Data.ImageData):
            image = Image.open(file_path)
            self.data.f_add_image(image)
            self.result = self.data.f_get_images()
            image.show()
        else:
            logger.error("Unsupported data type for parsing")


    def f_connect_toMongo(self) -> bool:
        # Code to connect to MongoDB goes here
        return False

    def f_get_data(self) -> list[dict[str, object] | Image.Image]:
        return self.result


    