

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

from Import import c_ImportData

from Data import Data, ImageData, TextData

test = True

def main():
    result = f_dataConvert_Import("Data.txt")

    result = f_dataConvert_Import("MockPicture.png")


def f_dataObjectConvert(data: Path) -> Data: # returns a Data object based on the file type
    if (data.suffix == ".png" or data.suffix == ".jpg" or data.suffix == ".jpeg"):
        return ImageData(str(data)) # data will be an instance of ImageData
    elif (data.suffix == ".txt"):
        return TextData(str(data)) # data will be an instance of TextData
    else:
        raise ValueError("Unsupported file type")

def f_importData(data: Data): # returns the imported Data object
    importer = c_ImportData(data)
    importer.f_parse()
    importer.f_import_toMongo()
    return importer.f_get_data()

def f_dataConvert_Import(file_name: str): # dataObjectConvert() + importData()
    data = Path(__file__).with_name(file_name)
    data_obj = f_dataObjectConvert(data)
    if test:
        print(f_importData(data_obj))

if __name__ == "__main__":
    main()