
'''
DocumentDB.py

Resource database subclass of Database for handling document-based storage (e.g., MongoDB).
'''
from Database import Database, MONGODB_URI, DB_NAME, COLLECTION_NAME, MAX_BINARY_SIZE

from contextlib import contextmanager
from pymongo import MongoClient

import mimetypes
from datetime import datetime, timezone
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
    

    # Builds the entry's natural key: "<parent folder path>/<name>" (just "<name>" at the root).
    def _entry_id(self, data) -> str:
        acName = Path(data.f_get_file_path()).name
        return f"{config.PARENT_FOLDER_PATH}/{acName}" if config.PARENT_FOLDER_PATH else acName

    # Builds the entry document; content is stored in the clear until an encryption step fills cyphertext/key_version.
    def _build_entry(self, data, pContent) -> dict:
        fpFilePath = Path(data.f_get_file_path())
        pEntry = {
            "entry_id": self._entry_id(data),
            "username": config.USERNAME,
            "key_version": None,
            "name": fpFilePath.name,
            "is_favorite": False,
            "date_modified": datetime.fromtimestamp(fpFilePath.stat().st_mtime, timezone.utc).isoformat(),
            "cyphertext": None,
            "plaintext_data": pContent,
            "parent_folder_id": config.PARENT_FOLDER_ID,
            "created_at": datetime.now(timezone.utc),
        }
        # Mirrors the SQL check constraint: exactly one of cyphertext / plaintext_data is set.
        if (pEntry["cyphertext"] is None) == (pEntry["plaintext_data"] is None):
            raise ValueError("Exactly one of cyphertext or plaintext_data must be set.")
        return pEntry

    def _add(self, pDB, data) -> None: 
        #COLLECTION_NAME is MongoDB's way for specifying the collection within the database
                pCollection = pDB[COLLECTION_NAME] 
                pCollection.create_index([("username", 1), ("entry_id", 1)], unique=True)   # primary key (username, entry_id)
                pCollection.create_index("username")
                
                # Check size: if file size > 16MB, then split the file into chunks via GrisFS. Then, store each file/chunk separately into the database.
                fpFilePath = Path(data.f_get_file_path())
                acEntryId = self._entry_id(data)

                if fpFilePath.stat().st_size > MAX_BINARY_SIZE:
                    from gridfs import GridFS
                    gfs = GridFS(pDB)    # Initialize GridFS, using the current database connection for storing large files
                    pEntry = self._build_entry(data, b"")   # metadata only: the content lives in the GridFS chunks
                    pMetadata = {k: pEntry[k] for k in ("username", "name", "is_favorite", "date_modified", "parent_folder_id", "created_at")}
                    with open(fpFilePath, "rb") as file:    # Open the file in binary read mode for storing in GridFS
                        gfs.put(file, filename=acEntryId, content_type=data.f_get_content_type(), metadata=pMetadata)
                    return  # Exit after storing the large file in chunks
                
                # Access the file, based on the content type: text, image, video, audio, or application
                if isinstance(data, Data.c_TextData): # for text files 
                    with open(fpFilePath, "r", encoding="utf-8") as file: pContent = file.read()

                else: # For binary data like images, videos, audio, or other application files
                    with open(fpFilePath, "rb") as file: pContent = file.read()

                # Insert the entry into the MongoDB collection
                pCollection.insert_one(self._build_entry(data, pContent))

                if (config.TEST_MODE): print(f"Added {data}")
                # MongoDB will report the statistics of the file, including its size, date of insertion, and other metadata.
    
    
    
    def _delete(self, pDB, data) -> None: 
        pCollection = pDB[COLLECTION_NAME]
        pCollection.delete_one({"username": config.USERNAME, "entry_id": self._entry_id(data)})
        if (config.TEST_MODE): print(f"Deleted {data}")




    def _query(self, pDB, data)-> str | Image.Image | bytes:    # return as text, image, video, audio, or binary data
        pCollection = pDB[COLLECTION_NAME]
        acFileName = Path(data.f_get_file_path()).name
        acEntryId = self._entry_id(data)
        pRetrievedName = pCollection.find_one({"username": config.USERNAME, "entry_id": acEntryId}) # Retrieve entry

        # Gets the file data from MongoDB, via the pRetrievedName document (<16MB) or from GridFS if larger (≥16MB)
        # if file is <16 MB
        if (pRetrievedName is not None):    # if pRetrievedName is not empty
            if pRetrievedName.get("plaintext_data") is None and pRetrievedName.get("cyphertext") is not None:
                raise NotImplementedError(f"ERROR: {acEntryId} is encrypted (key_version {pRetrievedName.get('key_version')}); decryption is not implemented.")
            aiFileBytes = pRetrievedName["plaintext_data"]
        else:   #if file is ≥16 MB (stored as GridFS chunks - refer to _add())
            from gridfs import GridFS
            gfs = GridFS(pDB)
            pGridFile = next(iter(gfs.find({"filename": acEntryId, "metadata.username": config.USERNAME}).sort("uploadDate", -1).limit(1)), None)
            aiFileBytes = pGridFile.read() if pGridFile is not None else None

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
                .find({"username": config.USERNAME}, {"name": 1})   # projection: skip the content columns
                .sort("_id", 1)                                     # oldest first, stable order
                .limit(limit))
        return [doc["name"] for doc in cursor]