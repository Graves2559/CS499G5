''' 
StorageNode.py


'''
from __future__ import annotations  # for Folder instance within StorageNode
import re
import config
from Item import Item
from enum import Enum


class EntryType(Enum):
    D = 1  # Page
    W = 2  # Chapter
    M = 3  # Volume
    Y = 4  # Series

class StorageNode:
    def __init__(self):
        self.name = ""
        self.parent: Folder = None
    
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

    # To identify a generic StorageNode (i.e. a Folder), its name (here, the
    # full path of names) is enough. File overrides this below, since a file
    # is identified by its name, entryType, AND entryNum together.
    def __repr__(self):
        return f"{type(self).__name__}('{self._path()}')"


class File(StorageNode):
    def __init__(self):
        super().__init__()
        self.entryType: EntryType = None
        self.entryNum: int = 0
        self.data: str = ""
        self.isFavorite: bool = False
        self.ItemList: list[Item] = []
        self.date_modified: str = ""  # Added date_modified attribute for sorting by date modified
        # DB round-tripping fields -- every File (encrypted or not) is now
        # persisted as soon as it's created (see e2e.create_page), so these
        # live on the base class rather than only on Security/EncryptedFile.py's
        # EncryptedFile subclass. None/empty until actually persisted.
        self.entryID = None            # DB primary key (a natural "<folder path>/<name>" key, not a surrogate one)
        self.username = ""              # Owning user; required for JournalEntryDatabaseAdapter.get/delete lookups
        self.parentFolderID = None     # FK to storage_folders(folder_id); which folder this entry is filed under
        self.creationTime = None       # DB row's created_at, once persisted

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

    def setParentFolderID(self, parentFolderID):
        if (config.TEST_MODE): print(f"\nSetting parent folder ID: {parentFolderID}")
        self.parentFolderID = parentFolderID
        if (config.TEST_MODE): print(f"Parent folder ID set to: {self.parentFolderID}")

    def getCreationTime(self):
        print(f"\nGetting creation time: {self.creationTime}")
        return self.creationTime

    def setCreationTime(self, creationTime):
        if (config.TEST_MODE): print(f"\nSetting creation time: {creationTime}")
        self.creationTime = creationTime
        if (config.TEST_MODE): print(f"Creation time set to: {self.creationTime}")

    # A file is identified by its name, entryType, and entryNum together
    # (unlike a generic StorageNode/Folder, which is identified by name alone).
    def __repr__(self):
        entryTypeName = self.entryType.name if self.entryType is not None else None
        return f"{type(self).__name__}('{self._path()}', entryType={entryTypeName}, entryNum={self.entryNum})"

    def getEntryType(self)->EntryType: 
        print(f"\nGetting entry type: {self.entryType}")
        return self.entryType

    def getEntryNum(self)->int: 
        print(f"\nGetting entry num: {self.entryNum}")
        return self.entryNum

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

    def setEntryType(self, entryType: EntryType): 
        if (config.TEST_MODE): print(f"\nSetting entry type: {entryType}")
        self.entryType = entryType
        if (config.TEST_MODE): print(f"Entry type set to: {self.entryType}")

    def setEntryNum(self, entryNum: int): 
        if (config.TEST_MODE): print(f"\nSetting entry num: {entryNum}")
        self.entryNum = entryNum
        if (config.TEST_MODE): print(f"Entry num set to: {self.entryNum}")

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
        duplicate.setEntryType(self.getEntryType())
        duplicate.setEntryNum(self.getEntryNum())
        duplicate.setFavorite(self.getFavorite())
        duplicate.setDateModified(self.getDateModified())
        return duplicate

    def displayContents(self):
        print(f"\nDisplaying contents of file: {self.getName()}")
        return self.entryType, self.entryNum, self.data, self.isFavorite, self.ItemList, self.date_modified

    # Marks each item's own content with its id, one item per line --
    # "(id): content". A file's data is the concatenation of all its items'
    # contents this way, so the file can be encrypted/stored as a single
    # blob while individual item content/position stay recoverable on
    # decrypt (see populateItemContentFromData). Assumes item content has
    # no embedded newlines -- multi-line item content is not supported by
    # this line-based format.
    _ITEM_LINE_PATTERN = re.compile(r"^\((-?\d+)\): (.*)$")

    # Recomputes self.position for every item (matching its actual index in
    # ItemList) and self.data as the join of every item's marked content.
    # Call this any time ItemList changes (add/edit/delete item) -- once a
    # file has items, its data is DERIVED from them, not independently set.
    def syncDataFromItems(self):
        for idx, item in enumerate(self.ItemList):
            item.set_position(idx)
        self.data = "\n".join(f"({item.get_id()}): {item.get_content()}" for item in self.ItemList)

    # The inverse of syncDataFromItems: fills in each existing ItemList
    # entry's .content by parsing self.data's "(id): content" markers,
    # matched by id. Used after decryption, where self.data holds the
    # decrypted marked text and self.ItemList already holds the matching
    # metadata (id/position/timestamp -- persisted separately, unencrypted;
    # see EncryptedFile.ItemList/Database.py) but not yet any content.
    def populateItemContentFromData(self):
        contentByID = {}
        for line in self.data.split("\n"):
            match = File._ITEM_LINE_PATTERN.match(line)
            if match:
                contentByID[int(match.group(1))] = match.group(2)
        for item in self.ItemList:
            if item.get_id() in contentByID:
                item.set_content(contentByID[item.get_id()])

    # StorageManager.Delete already removes this file from its parent's
    # children and clears its own .parent before calling this -- mirrors
    # Folder.delete()'s "clear what this node itself still owns" cleanup.
    def delete(self):
        if (config.TEST_MODE): print(f"\nDeleting file {self.name}")
        self.ItemList.clear()
        if (config.TEST_MODE): print(f"File {self.name} deleted")

class Folder(StorageNode):
    def __init__(self, isLocked: bool = False):
        super().__init__()
        self.children: list[StorageNode] = []
        self.isLocked = isLocked
        # DB round-tripping fields only (mirrors EncryptedFile.entryID/username
        # in Security/EncryptedFile.py) -- unused/None for in-memory-only
        # folders, set by StorageFolderDatabaseAdapter once persisted.
        self.folderID = None
        self.parentFolderID = None

    def getFolderID(self):
        print(f"\nGetting folder ID: {self.folderID}")
        return self.folderID

    def setFolderID(self, folderID):
        if (config.TEST_MODE): print(f"\nSetting folder ID: {folderID}")
        self.folderID = folderID
        if (config.TEST_MODE): print(f"Folder ID set to: {self.folderID}")

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
        


