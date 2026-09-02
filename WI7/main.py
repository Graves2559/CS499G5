

'''
main.py

Author: Trinh Pham

This is the executable script for the project.
This will instantiate the main classes of the project and inject the necessary dependencies.


'''

'''
Context: 
1. MongoDB is a NoSQL database that stores data in JSON, BSON, and XML documents.
2. NoSQL databases allow for horizontal scaling, such that there can be many servers instead of just one for storing data.
'''

'''
Objectives:
1. To import data into a MongoDB
    -> Requires a running MongoDB instance and code to connect to it.
2. Have mock data to import into the MongoDB database.

'''

from pathlib import Path

try:
    from .Import import c_ImportData
    from .Data import c_Data, c_ImageData, c_TextData
except ImportError:
    from Import import c_ImportData
    from Data import c_Data, c_ImageData, c_TextData

test = True

def main():
    result = f_dataConvert_Import("Data.txt")

    result = f_dataConvert_Import("MockPicture.png")


def f_dataObjectConvert(fpFilePath: Path) -> c_Data: # returns a Data object based on the file type
    if (fpFilePath.suffix == ".png" or fpFilePath.suffix == ".jpg" or fpFilePath.suffix == ".jpeg"):
        return c_ImageData(str(fpFilePath)) # data will be an instance of c_ImageData
    elif (fpFilePath.suffix == ".txt"):
        return c_TextData(str(fpFilePath)) # data will be an instance of c_TextData
    else:
        raise ValueError("Unsupported file type")

def f_importData(pData: c_Data): # returns the imported Data object (not sure yet whether to return anything or not)
    pImporter = c_ImportData(pData)
    pImporter.f_parse()
    pImporter.f_import_toMongo()
    return pImporter.f_get_data()

def f_dataConvert_Import(fpFileName: str): # dataObjectConvert() + importData()
    fpFilePath = Path(__file__).with_name(fpFileName)
    pDataObject = f_dataObjectConvert(fpFilePath)
    if test:
        print(f_importData(pDataObject))

if __name__ == "__main__":
    main()