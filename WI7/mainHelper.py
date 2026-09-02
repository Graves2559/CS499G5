
'''
mainHelper.py

Author: Trinh Pham

This file contains helper functions for the main executable script.

'''

from pathlib import Path

try:
    from .DBManager import c_DBManager
    from .Data import c_Data, c_ImageData, c_TextData
except ImportError:
    from DBManager import c_DBManager
    from Data import c_Data, c_ImageData, c_TextData


# A handler class for the main executable script
class c_MainHelper:
    def __init__(self, test: bool = False, deleteAll: bool = False) -> None:
        self.test = test
        self.deleteAll = deleteAll

        if deleteAll:
            dbManager = c_DBManager.f_get_instance(None)
            dbManager.f_deleteDataAll()


    def f_dataConvert_Import(self, acFileName: str) -> list:            # dataObjectConvert() + importData()
        fpFilePath = Path(__file__).with_name(acFileName)
        data = self.f_dataObjectConvert(fpFilePath)

        return self.f_importData(data)

    def f_dataObjectConvert(self, fpFilePath: Path) -> c_Data:              # returns a Data object based on the file type
        if fpFilePath.suffix.lower() in (".png", ".jpg", ".jpeg"):
            return c_ImageData(str(fpFilePath))
        elif fpFilePath.suffix.lower() == ".txt":
            return c_TextData(str(fpFilePath))
        else:
            raise ValueError("Unsupported file type")

    def f_importData(self, data: c_Data) -> list:                       # returns the imported Data object 
        pImporter = c_DBManager.f_get_instance(data)
        pImporter.f_parse()
        pImporter.f_import_toMongo()

        if self.test:
            pImporter.f_show()

        return pImporter.f_get_data()

    def f_retrieveDataDB(self, acFileName: str) -> list:                 # retrieves data from the database based on the file type
        fpFilePath = Path(__file__).with_name(acFileName)
        data = self.f_dataObjectConvert(fpFilePath)
        pImporter = c_DBManager.f_get_instance(data)
        pImporter.f_parse()
        pImporter.f_show()
        return pImporter.f_get_data()

    def f_deleteDataDB(self, acFileName: str) -> None:                 # deletes data from the database based on the file type
        fpFilePath = Path(__file__).with_name(acFileName)
        data = self.f_dataObjectConvert(fpFilePath)
        pImporter = c_DBManager.f_get_instance(data)
        pImporter.f_parse()
        pImporter.f_deleteData()