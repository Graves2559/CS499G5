'''
MongoContentStore.py

Implements the ContentStore port: the image/text/video bytes live in MongoDB (GridFS), so files of any size work.
The GridFS file _id is the media id stored in Postgres (index_entries.media_id).
'''
import gridfs
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from CommonErrors.Errors import NotFoundError


class MongoContentStore:
    def __init__(self, uri: str, database: str = "UserFiles"):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.fs = gridfs.GridFS(self.client[database])

    def put(self, username: str, entryId: str, content: bytes, contentType: str) -> str:
        return str(self.fs.put(content, filename=entryId, content_type=contentType, username=username))

    def get(self, mediaId: str) -> bytes:
        try:
            return self.fs.get(ObjectId(mediaId)).read()
        except (gridfs.errors.NoFile, InvalidId):
            raise NotFoundError("content")

    def delete(self, mediaId: str) -> None:
        self.fs.delete(ObjectId(mediaId))
