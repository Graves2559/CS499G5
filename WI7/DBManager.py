
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

import json                     # for handling JSON data
import logging                  # for logging errors and information
import mimetypes                # for image file (binary form, ≤16 MB). Tells MongoDB what kind of file the binary data represents.
import traceback                # To detail what line an error occurred on
from pathlib import Path        # for handling file paths
from PIL import Image           # If not installed in the mongoenv, run: python -m pip install Pillow pymongo

try:
    from . import Data
except ImportError:
    import Data


from pymongo import MongoClient
from bson.binary import Binary
from gridfs import GridFS


logger = logging.getLogger(__name__)
_CONSTRUCTOR_TOKEN = object()


# This class is a singleton, such that there is only one instance of it throughout the application.
# It will manage the interaction between the data and the database
class c_DBManager:
    # Data
    MONGODB_URI = "mongodb://localhost:27017/"
    DB_NAME = "admin"
    COLLECTION_NAME = "Test"
    MAX_BINARY_SIZE = 16 * 1024 * 1024                  # Maximum size for binary data (16 MB)
    _instance = None                                    # Singleton instance of the class
    
    data: Data.c_Data | None                            # for using Data object to access its methods (getFilePath and getData)
    result: list[dict[str, object] | Image.Image]       # Image(module from PIL).Image(an Image Object from said Module)
                                                        # A list of all Data objects that have been parsed and are ready for database operations


    # Methods

    # None data type is for when no Data object is provided during initialization (for deleteDataAll operation (see mainHelper constructor))
    def __new__(cls, data: Data.c_Data | None = None, _token: object = None): # The cls parameter represents the class itself, used for creating a singleton instance
        if _token is not _CONSTRUCTOR_TOKEN:                    # Ensures that the constructor is only called through the f_get_instance method
            raise TypeError("Use c_DBManager.f_get_instance() to access the DB manager")
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data: Data.c_Data | None = None, _token: object = None) -> None:
        if _token is not _CONSTRUCTOR_TOKEN:
            raise TypeError("Use c_DBManager.f_get_instance() to access the DB manager")
        self.data = data
        self.result = []

    @classmethod
    def f_get_instance(cls, data: Data.c_Data | None = None):
        return cls(data, _CONSTRUCTOR_TOKEN)            # Returns the singleton instance of the class

    def f_connect_toMongo(self) -> MongoClient | None:
        try:
            pClient = MongoClient(self.MONGODB_URI)
            pDb = pClient[self.DB_NAME]
            pCollection = pDb[self.COLLECTION_NAME]
            return pClient
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to connect to MongoDB at line {iLineNumber}: {e}")
            return None

    def f_deleteData(self) -> None:    # Deletes the specific data object from MongoDB
        try:
            pClient = MongoClient(self.MONGODB_URI)
            pDb = pClient[self.DB_NAME]
            pCollection = pDb[self.COLLECTION_NAME]
            pClient.close()
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to connect to MongoDB at line {iLineNumber}: {e}")
            return

        try:
            if isinstance(self.data, Data.c_TextData):
                aiIds = [doc["_id"] for doc in self.result if isinstance(doc, dict)]    # doc[_id] is the unique identifier of the document in MongoDB
                if aiIds:
                    pCollection.delete_many({"_id": {"$in": aiIds}})
            elif isinstance(self.data, Data.c_ImageData):
                acFileName = Path(self.data.f_get_file_path()).name
                pCollection.delete_many({"filename": acFileName})

                pGridFSFiles = pDb["fs.files"]                  # fs is MongoDB's GridFS collection for file metadata
                pGridFSChunks = pDb["fs.chunks"]                # fs.chunks stores the actual file data in chunks
                aFileIds = [
                    document["_id"]
                    for document in pGridFSFiles.find({"filename": acFileName})
                ]
                if aFileIds:
                    pGridFSFiles.delete_many({"_id": {"$in": aFileIds}})
                    pGridFSChunks.delete_many({"files_id": {"$in": aFileIds}})

            pClient.close()
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to delete from MongoDB at line {iLineNumber}: {e}")

    def f_deleteDataAll(self) -> None:              # Deletes all text and image files from MongoDB
        try:
            pClient = MongoClient(self.MONGODB_URI)
            pDb = pClient[self.DB_NAME]
            pCollection = pDb[self.COLLECTION_NAME]
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to connect to MongoDB at line {iLineNumber}: {e}")
            return

        try:
            pCollection.delete_many({})
            pDb["fs.files"].delete_many({})
            pDb["fs.chunks"].delete_many({})
            pClient.close()
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to delete from MongoDB at line {iLineNumber}: {e}")

    def f_get_data(self) -> list[dict[str, object] | Image.Image]:          # Not really used right now - just used as a getter for the future
        # Simply returns the result list, which contains the data retrieved from the Data object
        return self.result

    def f_import_toMongo(self) -> None:         # imports some data (text, image) into MongoDB
        try:
            pClient = MongoClient(self.MONGODB_URI)
            pDb = pClient[self.DB_NAME]
            pCollection = pDb[self.COLLECTION_NAME]
            pClient.close()
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to connect to MongoDB at line {iLineNumber}: {e}")
            return

        try:
            if isinstance(self.data, Data.c_TextData):
                pCollection.insert_many(self.result)
            elif isinstance(self.data, Data.c_ImageData):
                fpFilePath = self.data.f_get_file_path()
                acFileName = Path(fpFilePath).name
                acContentType = mimetypes.guess_type(fpFilePath)[0]
                acContentType = acContentType or "application/octet-stream"

                if Path(fpFilePath).stat().st_size <= self.MAX_BINARY_SIZE:     # If ≤16MB
                    with open(fpFilePath, "rb") as file:
                        abImageData = Binary(file.read())

                    pCollection.insert_one({
                        "filename": acFileName,
                        "content_type": acContentType,
                        "data": abImageData
                    })
                else:
                    with open(fpFilePath, "rb") as file:                        # If >16 MB
                        GridFS(pDb).put(
                            file,
                            filename=acFileName,
                            content_type=acContentType
                        )
            
            pClient.close()
        except Exception as e:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.exception(f"Failed to import to MongoDB at line {iLineNumber}: {e}")

    def f_parse(self) -> None:                                      # Parse the data file and populate the result list accordingly
        # Minimum guarantee: self.data must be a Data object before parsing
        if not isinstance(self.data, Data.c_Data):            # inverse guard clause
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.error(f"parse() requires a Data object at line {iLineNumber}")
            return

        fpFilePath = self.data.f_get_file_path()    # More writability for subsequent file operations

        if isinstance(self.data, Data.c_TextData):
            try:
                with open(fpFilePath, 'r') as file:
                    self.result = [json.loads(acLine) for acLine in file if acLine.strip()]
            except json.JSONDecodeError:
                self.result = []
                iLineNumber = traceback.extract_stack()[-1].lineno
                logger.exception(f"parse() failed to parse JSON at line {iLineNumber}")
        elif isinstance(self.data, Data.c_ImageData):
            try:
                pImage = Image.open(fpFilePath)
                self.data.f_add_image(pImage)
                self.result = self.data.f_get_images()
            except (Image.UnidentifiedImageError, OSError):
                self.result = []
                iLineNumber = traceback.extract_stack()[-1].lineno
                logger.error(f"Invalid image file at line {iLineNumber}: {fpFilePath}")
        else:
            iLineNumber = traceback.extract_stack()[-1].lineno
            logger.error(f"Unsupported data type for parsing at line {iLineNumber}")

    def f_show(self) -> None:                                         # Show a preview of the data (first and last items if more than 2)    
        # Size of the preview list optimization
        if len(self.result) <= 2:
            aPreview = self.result
        else:
            aPreview = [self.result[0], self.result[-1]]

        # showing the preview of the data
        if isinstance(self.data, Data.c_TextData):
            for doc in aPreview:
                print(doc)
        elif isinstance(self.data, Data.c_ImageData):
            for img in aPreview:
                if isinstance(img, Image.Image):
                    img.show()


    