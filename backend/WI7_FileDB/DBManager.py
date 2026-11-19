
'''
DBManager.py

Database manager class for handling database operations.

'''

from documentDB import DocumentDB
from Data import c_Data
from passwordDB import PasswordDB
from PIL import Image
import Data
import config

class DBManager:
    def __init__(self):
        # Initialize the database connection or any required resources
        self.db = DocumentDB()  # Initialize the default database as DocumentDB
    
    def add_to_db(self, inputs):
        dataList = []
        for item in inputs:
            convertedDataClass = c_Data(item).f_convert_to_data_class()
            dataList.append(convertedDataClass)
        self.db.add_to_database(dataList) 

    def delete_from_db(self, inputs):
        dataList = []
        for item in inputs:
            convertedDataClass = c_Data(item).f_convert_to_data_class()
            dataList.append(convertedDataClass)
        self.db.delete_from_database(dataList)

    def edit_in_db(self, identifier, new_data):
        # TODO: Implement the logic for editing/updating entries in the database. Convert the identifier and new_data to the appropriate data classes if necessary.
        self.db.update_database(identifier, new_data)

    def query_from_db(self, inputs):
        dataList = []
        for item in inputs:
            convertedDataClass = c_Data(item).f_convert_to_data_class()
            dataList.append(convertedDataClass)
        
        results = self.db.query_database(dataList)
        if (config.TEST_MODE): self.showFiles(dataList, results)    # Will only use showFiles() here. LIST_ALL will not use showFiles().
        return results

    def list_all_from_db(self):
        limit = config.LIST_LIMIT  
        names =self.db.list_all_from_database(limit)
        if config.TEST_MODE: 
            for i,name in enumerate (names,1): print(f"{i}. {name}")
        return names

    def setDB(self, db):
        self.db = db

    def showFiles(self, dataList, results):
        for data, result in zip(dataList, results):
            if result is None: continue
            if isinstance(data, Data.c_TextData): print(result)
            elif isinstance(data, Data.c_ImageData): result.show()
            elif isinstance(data, Data.c_VideoData): self._open_video(result)
            elif data.f_get_content_type() == "application/pdf" and isinstance(result, bytes):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pTempFile:
                    pTempFile.write(result)
                self._open_video(pTempFile.name)
            else: print(f"{len(result)} bytes (not displayable)")



    # private
    def _open_video(self, file_path):
        # Implement the logic to open and play the video file using an appropriate library or system call.
        import subprocess
        import platform

        if platform.system() == "Darwin":  subprocess.call(["open", file_path]) # macOS
        elif platform.system() == "Windows":  subprocess.call(["start", file_path], shell=True) # Windows
        else:  subprocess.call(["xdg-open", file_path]) # Linux and other platforms
