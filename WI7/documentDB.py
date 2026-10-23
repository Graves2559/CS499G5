
'''
DocumentDB.py

Resource database subclass of Database for handling document-based storage (e.g., MongoDB).
'''
from Database import Database, MONGODB_URI, DB_NAME, COLLECTION_NAME, MAX_BINARY_SIZE

from contextlib import contextmanager
from pymongo import MongoClient

import mimetypes
from pathlib import Path

from PIL import Image
import Data
# import TemporaryCache

import config


class DocumentDB(Database):                
    _instance = None                                    

    data: Data.c_Data | None                           
    result: list[dict[str, object] | Image.Image | str] 
    # temp_cache: TemporaryCache.c_TemporaryCache


    def __init__(self):
        super().__init__()

    def connect(self):
        # Implement the logic to connect to the document database (e.g., MongoDB)
        return self.automatically_manage_connection()

    def add_to_database(self, data) -> None:   # Combining frequent addition logic for once and batch additions
        results, failures = self.persistConnection(self._add, data, "add")
        if (config.TEST_MODE): 
            print(f"\nFinished executing add_to_database().\n")
            if(failures == 0): print(f"\nSuccessfully added all of {data}.\n")
            else: print(f"\nERROR: Failed to add some of {data}.\n")


    def delete_from_database(self, data):   # Combining frequent deletion logic for once and batch deletions
        results, failures = self.persistConnection(self._delete, data, "delete")
        if (config.TEST_MODE): 
            print(f"\nFinished executing delete_from_database().\n") 
            if(failures == 0): print(f"\nSuccessfully deleted all of {data}.\n")
            else: print(f"\nERROR: Failed to delete some of {data}.\n")


    def update_database(self, data):
        # Implement the logic to update data in the document database
        pass

    def query_database(self, data):
        # Implement the logic to query data from the document database
        results, failures = self.persistConnection(self._query, data, "query") 
        return results

        

    def list_all_from_database(self, limit):
        results, failures = self.persistConnection(self._list, [limit], "list")
        return results[0] if results else []

    


    # Opens the DB connection and then waits for all operations to complete before closing the connection.
    @contextmanager
    def automatically_manage_connection(self):
        pClient = MongoClient(MONGODB_URI)
        try:
            if (config.TEST_MODE): print("\nConnection establishing...\n")
            yield pClient[DB_NAME]     # pause the function here such that the other functions outside of this 
                                            # function is executed before resuming to the finally statement, 
                                            # closing the connection.
        finally:
            pClient.close()
            if (config.TEST_MODE): print("\nConnection closed.")

    # Because DBmanager will add, delete, edit, etc. iteratively, we need a way to persist the connection across multiple operations.
    def persistConnection(self, operation, items, action):
        results = []
        failures = 0
        try:
            with self.connect() as pDB:              # connect once for the whole batch
                for item in items:
                    try:
                        results.append(operation(pDB, item))
                        if (config.TEST_MODE): print(f"Successfully {action}: {item}")
                    
                    except Exception as e:           # one failure doesn't stop the rest
                        print(f"ERROR: Failed to {action} {item}: {e}")
                        results.append(None)  # Successful operations (add,delete) are returned as None
                                                # Failed operations do not (that is, there is no return value), 
                                                # which mess up the results alignment with the input items.
                        failures += 1
        except Exception as e:                       # connection-level failure
            print(f"ERROR: Failed to connect for {action}: {e}")
            failures += len(items)
        
        # failed items summary
        if failures > 0: print(f"{failures} items failed to {action}.") 

        return results, failures
    

    def _add(self, pDB, data) -> None: 
        #COLLECTION_NAME is MongoDB's way for specifying the collection within the database
                pCollection = pDB[COLLECTION_NAME] 
                
                # Check size: if file size > 16MB, then split the file into chunks via GrisFS. Then, store each file/chunk separately into the database.
                fpFilePath = Path(data.f_get_file_path())
                acFileName = fpFilePath.name

                if fpFilePath.stat().st_size > MAX_BINARY_SIZE:
                    from gridfs import GridFS
                    gfs = GridFS(pDB)    # Initialize GridFS, using the current database connection for storing large files
                    with open(fpFilePath, "rb") as file:    # Open the file in binary read mode for storing in GridFS
                        gfs.put(file, filename=acFileName, content_type=data.f_get_content_type())
                    return  # Exit after storing the large file in chunks
                
                # Access the file, based on the content type: text, image, video, audio, or application
                if isinstance(data, Data.c_TextData): # for text files 
                    with open(fpFilePath, "r", encoding="utf-8") as file: pContent = file.read()

                else: # For binary data like images, videos, audio, or other application files
                    with open(fpFilePath, "rb") as file: pContent = file.read()

                # Insert the accessed file into the MongoDB collection with its filename, content type, and data
                pCollection.insert_one({"filename": acFileName, "content_type": data.f_get_content_type(), "data": pContent})

                if (config.TEST_MODE): print(f"Added {data}")
                # MongoDB will report the statistics of the file, including its size, date of insertion, and other metadata.
    
    
    
    def _delete(self, pDB, data) -> None: 
        pCollection = pDB[COLLECTION_NAME]
        acFileName = Path(data.f_get_file_path()).name
        pCollection.delete_one({"filename": acFileName})
        if (config.TEST_MODE): print(f"Deleted {data}")




    def _query(self, pDB, data)-> str | Image.Image | bytes:    # return as text, image, video, audio, or binary data
        pCollection = pDB[COLLECTION_NAME]
        acFileName = Path(data.f_get_file_path()).name
        pRetrievedName = pCollection.find_one({"filename": acFileName}) # Retrieve file

        # Gets the file data from MongoDB, via the pRetrievedName document (<16MB) or from GridFS if larger (≥16MB)
        # if file is <16 MB
        if (pRetrievedName is not None): aiFileBytes = pRetrievedName["data"]     # if pRetrievedName is not empty
        else:   #if file is ≥16 MB (stored as GridFS chunks - refer to _add())
            from gridfs import GridFS
            gfs = GridFS(pDB)
            if gfs.exists({"filename": acFileName}):
                aiFileBytes = gfs.get_last_version(acFileName).read()
            else:
                aiFileBytes = None

        if aiFileBytes is None: raise FileNotFoundError(f"ERROR: File {acFileName} not found in MongoDB")

        # Convert the bytes back to their proper format
        from io import BytesIO
        import tempfile
        if isinstance(data, Data.c_TextData): return aiFileBytes.decode("utf-8", errors="replace") if isinstance(aiFileBytes, bytes) else aiFileBytes
        if isinstance(data, Data.c_ImageData): return Image.open(BytesIO(aiFileBytes)) if isinstance(aiFileBytes, (bytes, bytearray)) else None
        if isinstance(data, Data.c_VideoData): 
            with tempfile.NamedTemporaryFile(suffix=Path(acFileName).suffix, delete=False) as pTempFile:
                pTempFile.write(aiFileBytes)
            return pTempFile.name

        return aiFileBytes

    def _list(self, pDB, limit):
        cursor = (pDB[COLLECTION_NAME]
                .find({}, {"filename": 1, "content_type": 1})   # projection: skip "data"
                .sort("_id", 1)                                 # oldest first, stable order
                .limit(limit))
        return [doc["filename"] for doc in cursor]