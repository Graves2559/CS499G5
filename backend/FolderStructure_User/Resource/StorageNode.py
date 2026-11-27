''' 
StorageNode.py


'''
from __future__ import annotations  # for Folder instance within StorageNode
import uuid

from FolderStructure_User import config


class StorageNode:
    def __init__(self):
        self.name = ""
        self.parent: Folder = None
        self.deletedAt = None  # ISO-8601 timestamp once soft-deleted into Trash; see setDeletedAt below
    
    def getName(self):
        print(f"\nGetting name: {self.name}")
        return self.name

    def setName(self, name):
        raise BaseException("setName method to be used within subclass")

    def move(self, destination: Folder):
        raise BaseException("move method to be used within subclass")
    
    def delete(self):
        raise BaseException("delete method to be used within subclass")

    def setParent(self, parent: Folder):
        if (config.TEST_MODE): print(f"\nSetting parent: {parent}")
        self.parent = parent
        if (config.TEST_MODE): print(f"Parent set to: {self.parent}")

    def getParent(self):
        print(f"\nGetting parent: {self.parent}")
        return self.parent

    def getDeletedAt(self):
        print(f"\nGetting deleted at: {self.deletedAt}")
        return self.deletedAt

    # Set by StorageManager.Delete when this node is soft-deleted into Trash
    # (an ISO-8601 timestamp); None otherwise. StorageManager.PurgeExpiredTrash
    # compares this against the grace period to decide when to erase it for
    # real, and StorageManager.Move clears it back to None if the node is
    # moved out of Trash (i.e. restored) before that happens.
    def setDeletedAt(self, deletedAt):
        if (config.TEST_MODE): print(f"\nSetting deleted at: {deletedAt}")
        self.deletedAt = deletedAt
        if (config.TEST_MODE): print(f"Deleted at set to: {self.deletedAt}")

    # Without this, printing a node (e.g. in the many config.TEST_MODE debug
    # prints throughout StorageManager.py) falls back to Python's default
    # <StorageNode.File object at 0x...> -- showing the class name, but
    # nothing about where the node actually lives in the tree. This instead
    # walks up .parent to build the full path from the root, e.g.
    # File('Root/Input/2026-10-31').
    def _path(self) -> str:
        path = self.name
        node = self.parent
        while node is not None:
            path = f"{node.name}/{path}"
            node = node.parent
        return path

    # To identify a generic StorageNode (i.e. a Folder or File), its name
    # (here, the full path of names) is enough.
    def __repr__(self):
        return f"{type(self).__name__}('{self._path()}')"


class File(StorageNode):
    def __init__(self):
        super().__init__()
        self.data: str = ""
        self.isFavorite: bool = False
        self.date_modified: str = ""  # Added date_modified attribute for sorting by date modified
        # DB round-tripping fields -- every File (encrypted or not) is now
        # persisted as soon as it's created, so these live on the base class.
        # None/empty until actually persisted.
        self.entryID = None            # Name of the file 

        self.username = ""              # Owning user; required for JournalEntryDatabaseAdapter.get/delete lookups
        self.parentFolderID = None     # name of the parent folder
        self.parentFolderUniqueID = None  # unique ID of the parent folder

        self.creationTime = None       # DB row's created_at, once persisted

        # Generated once per file (not derived from its name/entryID, which
        # are only unique within a single folder) so it stays a stable,
        # globally-unique reference -- this is what child/related records
        # point back to via parentFolderUniqueID-style fields.
        self.fileUniqueID: str = str(uuid.uuid4())

    def getFileUniqueID(self) -> str:
        print(f"\nGetting file unique ID: {self.fileUniqueID}")
        return self.fileUniqueID

    def setFileUniqueID(self, fileUniqueID: str):
        if (config.TEST_MODE): print(f"\nSetting file unique ID: {fileUniqueID}")
        self.fileUniqueID = fileUniqueID
        if (config.TEST_MODE): print(f"File unique ID set to: {self.fileUniqueID}")

    def getEntryID(self):
        print(f"\nGetting entry ID: {self.entryID}")
        return self.entryID

    def setEntryID(self, entryID):
        if (config.TEST_MODE): print(f"\nSetting entry ID: {entryID}")
        self.entryID = entryID
        if (config.TEST_MODE): print(f"Entry ID set to: {self.entryID}")

    def getUsername(self) -> str:
        print(f"\nGetting username: {self.username}")
        return self.username

    def setUsername(self, username: str):
        if (config.TEST_MODE): print(f"\nSetting username: {username}")
        self.username = username
        if (config.TEST_MODE): print(f"Username set to: {self.username}")

    def getParentFolderID(self):
        print(f"\nGetting parent folder ID: {self.parentFolderID}")
        return self.parentFolderID

    def getParentFolderUniqueID(self):
        print(f"\nGetting parent folder unique ID: {self.parentFolderUniqueID}")
        return self.parentFolderUniqueID

    def setParentFolderID(self, parentFolderID):
        if (config.TEST_MODE): print(f"\nSetting parent folder ID: {parentFolderID}")
        self.parentFolderID = parentFolderID
        if (config.TEST_MODE): print(f"Parent folder ID set to: {self.parentFolderID}")

    def setParentFolderUniqueID(self, parentFolderUniqueID):
        if (config.TEST_MODE): print(f"\nSetting parent folder unique ID: {parentFolderUniqueID}")
        self.parentFolderUniqueID = parentFolderUniqueID
        if (config.TEST_MODE): print(f"Parent folder unique ID set to: {self.parentFolderUniqueID}")

    def getCreationTime(self):
        print(f"\nGetting creation time: {self.creationTime}")
        return self.creationTime

    def setCreationTime(self, creationTime):
        if (config.TEST_MODE): print(f"\nSetting creation time: {creationTime}")
        self.creationTime = creationTime
        if (config.TEST_MODE): print(f"Creation time set to: {self.creationTime}")

    def getData(self)->str: 
        print(f"\nGetting data: {self.data}")
        return self.data

    def getDateModified(self)->str:
        print(f"\nGetting date modified: {self.date_modified}")
        return self.date_modified

    def getFavorite(self)->bool: 
        print(f"\nGetting favorite status: {self.isFavorite}")
        return self.isFavorite

    def setName(self, fileName: str):  # str to be a date
        if (config.TEST_MODE): print(f"\nSetting file name: {fileName}")
        self.name = fileName
        if (config.TEST_MODE): print(f"File name set to: {self.name}")

    def setData(self, data: str): 
        if (config.TEST_MODE): print(f"\nSetting data: {data}")
        self.data = data
        if (config.TEST_MODE): print(f"Data set to: {self.data}")

    def setFavorite(self, isFavorite: bool):
        if (config.TEST_MODE): print(f"\nSetting favorite status: {isFavorite}")
        self.isFavorite = isFavorite
        if (config.TEST_MODE): print(f"Favorite status set to: {self.isFavorite}")

    def setDateModified(self, date_modified: str):
        if (config.TEST_MODE): print(f"\nSetting date modified: {date_modified}")
        self.date_modified = date_modified
        if (config.TEST_MODE): print(f"Date modified set to: {self.date_modified}")

    def deepCopy(self) -> File:
        duplicate = File()
        duplicate.setName(self.getName())
        duplicate.setData(self.getData())
        duplicate.setFavorite(self.getFavorite())
        duplicate.setDateModified(self.getDateModified())
        return duplicate

    def displayContents(self):
        print(f"\nDisplaying contents of file: {self.getName()}")
        return self.data, self.isFavorite, self.date_modified

    # StorageManager.Delete already removes this file from its parent's
    # children and clears its own .parent before calling this -- mirrors
    # Folder.delete()'s "clear what this node itself still owns" cleanup.
    def delete(self):
        if (config.TEST_MODE): print(f"\nDeleting file {self.name}")
        if (config.TEST_MODE): print(f"File {self.name} deleted")

class Folder(StorageNode):
    def __init__(self, isLocked: bool = False):
        super().__init__()
        self.children: list[StorageNode] = []
        self.isLocked = isLocked
        # DB round-tripping fields only (mirrors File.entryID/username above)
        # -- unused/None for in-memory-only folders, set by a DB adapter once
        # persisted.
        self.folderID = None
        self.parentFolderID = None

        # Generated once per folder, for the same reason as File.fileUniqueID
        # above: a folder's name is only unique within its own parent, not
        # globally, so children reference this as their parentFolderUniqueID.
        self.folderUniqueID: str = str(uuid.uuid4())

        # RQ4(f)/RQ4(c): folders can be favorited directly, independently of
        # any files/subfolders inside them -- favoriting a folder does not
        # cascade to its contents, nor relocate it anywhere.
        self.isFavorite: bool = False
        # RQ3: lets folders be sorted by creation date, the same way a
        # File's date_modified sorts files -- folders have no "modified"
        # concept here, only "created".
        self.date_created: str = ""

    def getFavorite(self) -> bool:
        print(f"\nGetting favorite status: {self.isFavorite}")
        return self.isFavorite

    def setFavorite(self, isFavorite: bool):
        if (config.TEST_MODE): print(f"\nSetting favorite status: {isFavorite}")
        self.isFavorite = isFavorite
        if (config.TEST_MODE): print(f"Favorite status set to: {self.isFavorite}")

    def getDateCreated(self) -> str:
        print(f"\nGetting date created: {self.date_created}")
        return self.date_created

    def setDateCreated(self, date_created: str):
        if (config.TEST_MODE): print(f"\nSetting date created: {date_created}")
        self.date_created = date_created
        if (config.TEST_MODE): print(f"Date created set to: {self.date_created}")

    def getFolderID(self):
        print(f"\nGetting folder ID: {self.folderID}")
        return self.folderID

    def setFolderID(self, folderID):
        if (config.TEST_MODE): print(f"\nSetting folder ID: {folderID}")
        self.folderID = folderID
        if (config.TEST_MODE): print(f"Folder ID set to: {self.folderID}")

    def getFolderUniqueID(self) -> str:
        print(f"\nGetting folder unique ID: {self.folderUniqueID}")
        return self.folderUniqueID

    def setFolderUniqueID(self, folderUniqueID: str):
        if (config.TEST_MODE): print(f"\nSetting folder unique ID: {folderUniqueID}")
        self.folderUniqueID = folderUniqueID
        if (config.TEST_MODE): print(f"Folder unique ID set to: {self.folderUniqueID}")

    def getParentFolderID(self):
        print(f"\nGetting parent folder ID: {self.parentFolderID}")
        return self.parentFolderID

    def setParentFolderID(self, parentFolderID):
        if (config.TEST_MODE): print(f"\nSetting parent folder ID: {parentFolderID}")
        self.parentFolderID = parentFolderID
        if (config.TEST_MODE): print(f"Parent folder ID set to: {self.parentFolderID}")

    def Add(self, node: StorageNode): 
        if (config.TEST_MODE): print(f"\nAdding node {node.getName()} to folder {self.name}")
        self.children.append(node)
        if isinstance(node, File):
            node.setParent(self)
        elif isinstance(node, Folder):
            node.setParent(self)
        if (config.TEST_MODE): print(f"Node {node.getName()} added to folder {self.name}")

    def Remove(self, node: StorageNode): 
        if (config.TEST_MODE): print(f"\nRemoving node {node.getName()} from folder {self.name}")
        self.children.remove(node)
        if (config.TEST_MODE): print(f"Node {node.getName()} removed from folder {self.name}")

    def setName(self, name):
        if (config.TEST_MODE): print(f"\nSetting folder name: {name}")
        self.name = name
        if (config.TEST_MODE): print(f"Folder name set to: {self.name}")

    def move(self, destination: Folder):
        if (config.TEST_MODE): print(f"\nMoving folder {self.name} to destination {destination.getName()}")
        destination.Add(self)
        if (config.TEST_MODE): print(f"Folder {self.name} moved to destination {destination.getName()}")

    def delete(self):
        if (config.TEST_MODE): print(f"\nDeleting folder {self.name}")
        self.children.clear()
        if (config.TEST_MODE): print(f"Folder {self.name} deleted")

    def getChildren(self):
        print(f"\nGetting children of folder {self.name}")
        return self.children
        


