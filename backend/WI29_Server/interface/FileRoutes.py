'''
FileRoutes.py

HTTP routes for a signed-in user's folders and files (all need the session cookie):
    GET   /api/entries             folders and files (metadata only)
    POST  /api/folders             {id, parentId, name, description}
    PATCH /api/entries/{id}        {name?, description?, favorite?}   (favorite: files only)
    PUT   /api/files/{id}          multipart: parentId, name, description, file (create or replace)
    GET   /api/files/{id}/content  download the file content
'''
from typing import List, Optional, Union
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Header, Response, UploadFile

from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.FileService import FileService
from WI29_Server.domain.Files import MAX_FILE_BYTES, FileEntry, Folder
from WI29_Server.interface.Schemas import EntryPatch, FolderBody
from WI29_Server.interface.Session import makeCurrentUser

SYMMETRIC_KEY_HEADER = "X-Symmetric-Key"


def entryToJson(entry: Union[Folder, FileEntry]) -> dict:
    if isinstance(entry, Folder):
        return {"id": entry.id, "parentId": entry.parentId, "name": entry.name, "kind": "folder",
                "description": entry.description}
    return {"id": entry.id, "parentId": entry.parentId, "name": entry.name, "kind": "file",
            "description": entry.description, "mimeType": entry.contentType, "size": entry.size,
            "favorite": entry.favorite, "dateModified": entry.dateModified, "encrypted": entry.keyVersion is not None}


def buildFileRouter(auth: AuthService, files: FileService) -> APIRouter:
    router = APIRouter()
    currentUser = makeCurrentUser(auth)

    @router.get("/api/entries")
    def listEntries(username: str = Depends(currentUser)) -> List[dict]:
        return [entryToJson(entry) for entry in files.listEntries(username)]

    @router.post("/api/folders")
    def createFolder(body: FolderBody, username: str = Depends(currentUser)):
        files.createFolder(username, body.id, body.parentId, body.name, body.description)
        return {"id": body.id}

    @router.patch("/api/entries/{entry_id}")
    def updateEntry(entry_id: str, body: EntryPatch, username: str = Depends(currentUser)):
        files.updateEntry(username, entry_id, body.name, body.description, body.favorite)
        return {"id": entry_id}

    # symmetricKey, when given (encryption is opt-in per upload), encrypts the content at rest.
    @router.put("/api/files/{entry_id}")
    def putFile(entry_id: str, parentId: str = Form(...), name: str = Form(...), description: str = Form(""),
                file: UploadFile = File(...), symmetricKey: Optional[str] = Form(None),
                username: str = Depends(currentUser)):
        content = file.file.read(MAX_FILE_BYTES + 1)  # one byte over the limit is enough to reject it
        size, contentType = files.putFile(username, entry_id, parentId, name, description, content, symmetricKey)
        return {"id": entry_id, "size": size, "mimeType": contentType}

    # The symmetric key travels as a header, never a query parameter (query strings end up in server/proxy
    # logs); required only when the stored file is actually encrypted.
    @router.get("/api/files/{entry_id}/content")
    def getContent(entry_id: str, username: str = Depends(currentUser),
                   symmetricKey: Optional[str] = Header(None, alias=SYMMETRIC_KEY_HEADER)):
        content, contentType, name = files.getContent(username, entry_id, symmetricKey)
        return Response(content, media_type=contentType, headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        })

    return router
