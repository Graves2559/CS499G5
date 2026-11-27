
'''
Database.py

Resource Database Base class for each database resource.

2 Database Resources:
1. SQL -> PostgreSQL (for now): for **PASSWORD HASH** storage and management.
    Note: PostgreSQL can be ran as a Docker container and can scale with any cloud provider (given that 
    you do use cloud storage: e.g., Azure, AWS, Google Cloud)
2. NoSQL -> MongoDB (for now): for input and output **FILES** (including images and videos)
    Note: MongoDB is used for storing documents. 

'''

# --- MongoDB configuration ---
MONGODB_URI = "mongodb://localhost:27017/"
DB_NAME = "Database"
COLLECTION_NAME = "admin"
MAX_BINARY_SIZE = 16 * 1024 * 1024      # 16 * 1 MB, or 16MB 

# --- Entry document fields (one document per entry in the collection) ---
# Primary key: (username, entry_id). Exactly one of cyphertext / plaintext_data must be set.
#   entry_id          str        "<parent folder path>/<name>"
#   username          str
#   key_version       int|None   key that wrapped the data key; None until encrypted
#   name              str        file name
#   is_favorite       bool       default False
#   date_modified     str        ISO-8601 timestamp
#   cyphertext        bytes|None encrypted content; None until encrypted
#   plaintext_data    str|bytes|None  content in the clear; None once encrypted
#   parent_folder_id  str|None
#   created_at        datetime   UTC
ENTRY_FIELDS = (
    "entry_id", "username", "key_version", "name", "is_favorite", "date_modified",
    "cyphertext", "plaintext_data", "parent_folder_id", "created_at",
)

class Database:
    def __init__(self):
        pass

    def connect(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def add_to_database(self, data):
        raise NotImplementedError("Subclasses should implement this method.")

    def delete_from_database(self, data):
        raise NotImplementedError("Subclasses should implement this method.")

    def update_database(self, data):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def query_database(self, query):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def list_all_from_database(self):
        raise NotImplementedError("Subclasses should implement this method.")

    