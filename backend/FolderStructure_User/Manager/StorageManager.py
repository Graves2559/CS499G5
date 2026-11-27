'''
StorageManager.py

'''
import re
from datetime import datetime, timedelta, timezone

from FolderStructure_User import config
from FolderStructure_User.Resource.StorageNode import StorageNode, File, Folder
from FolderStructure_User.Transformer.Sorter import Sorter, SortMetric

class StorageManager:
    # RQ6/RQ13: a soft-deleted node sits in Trash for this long before
    # PurgeExpiredTrash erases it for real.
    GRACE_PERIOD = timedelta(days=30)

    def __init__(self): 
        self.root: Folder = Folder()    # The repository root directory itself (the entry point into the repository)
        self.favorites: Folder = Folder()
        self.input: Folder = Folder()
        self.output: Folder = Folder()
        self.trash: Folder = Folder()

        self.root.setName("Root")
        self.favorites.setName("Favorites")  # Plain folder; favoriting (RQ4) no longer relocates anything here.
        self.input.setName("Input")          # Plain folder: files and subfolders can be added/moved freely.
        self.output.setName("Output")        # Plain folder: files and subfolders can be added/moved freely.
        self.trash.setName("Trash")          # Holds soft-deleted nodes during their grace period (RQ6/RQ13).

        self.Add(self.favorites, self.root)
        self.Add(self.input, self.root)
        self.Add(self.output, self.root)
        self.Add(self.trash, self.root)

        self.sorter = Sorter()
        
        
    def DisplayAll(self, metric: SortMetric): 
        if not isinstance(metric, SortMetric):
            raise TypeError(f"metric must be a SortMetric, got {type(metric).__name__}")

        if (config.TEST_MODE): print(f"\n====== StorageManager.DisplayAll ======")
        if (config.TEST_MODE): print(f"Displaying all contents of the root folder...")

        self.sorter.SortByMetric(self.root.children, metric)

        self.DisplayFolder(self.root, metric)
        if (config.TEST_MODE): print(f"====== End StorageManager.DisplayAll ======\n")

    # Recursive function to display all contents of a folder.
    def DisplayFolder(self, folder: Folder, metric: SortMetric):
        if not isinstance(metric, SortMetric):
            raise TypeError(f"metric must be a SortMetric, got {type(metric).__name__}")
            
        self.sorter.SortByMetric(folder.children, metric)

        if (config.TEST_MODE): print(f"\n====== StorageManager.DisplayFolder ======")
        if (config.TEST_MODE): print(f"Displaying folder: {folder}...")
        if (config.TEST_MODE): print(f"Folder: {folder}\n, name: {folder.getName()}\n, parent: {folder.getParent()}")

        for child in folder.children:
            if (isinstance(child, Folder)):
                self.DisplayFolder(child, metric)
            else:
                if (config.TEST_MODE): print(f"File: {child}\n, name: {child.getName()}\n, parent: {child.getParent()}")

        if (config.TEST_MODE): print(f"Displayed all contents of folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.DisplayFolder ======\n")

    def DisplayFile(self, file: File):
        if (config.TEST_MODE): print(f"\n====== StorageManager.DisplayFile ======")
        if (config.TEST_MODE): print(f"Displaying file: {file}...")
        if (config.TEST_MODE): print(f"File: {file}\n, name: {file.getName()}\n, parent: {file.getParent()}")
        
        if (config.TEST_MODE): print(f"Contents of file:")
        print(file.displayContents())
        if (config.TEST_MODE): print(f"Displayed contents of file: {file}")
        if (config.TEST_MODE): print(f"====== End StorageManager.DisplayFile ======\n")

    # Adds file or folder to a folder.
    # RQ5: names must be unique within a folder (a blank/unset name is not
    # considered a "name" yet, so it's exempt -- CreateFile/CreateFolder
    # below always assign a real one).
    def Add(self, node: StorageNode, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Add ======")
        if (config.TEST_MODE): print(f"Adding node: {node} to folder: {folder}...")

        name = node.getName()
        if name:
            existing_names = {child.getName() for child in folder.children if child is not node}
            if name in existing_names:
                if (config.TEST_MODE): print(f"====== End StorageManager.Add ======\n")
                raise ValueError(f"A node named '{name}' already exists in folder: {folder}")

        if (config.TEST_MODE): print(f"{node}: {node.getName()}\n, parent: {node.getParent()}")
        if (config.TEST_MODE): print(f"Folder: {folder}: {folder.getName()}\n, children: {folder.children}\n, parent: {folder.getParent()}")

        folder.children.append(node)
        node.setParent(folder)

        if (config.TEST_MODE): print(f"Node added: {node} to folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.Add ======\n")

    def Rename(self, node: StorageNode, new_name:str): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Rename ======")
        if (config.TEST_MODE): print(f"Renaming node: {node} to new name: {new_name}...")
        if (config.TEST_MODE): print(f"Current name of node: {node.getName()}\n, parent: {node.getParent()}")

        # RQ5/RQ7: the new name must stay unique among its siblings too.
        if new_name and node.getParent() is not None:
            existing_names = {child.getName() for child in node.getParent().getChildren() if child is not node}
            if new_name in existing_names:
                if (config.TEST_MODE): print(f"====== End StorageManager.Rename ======\n")
                raise ValueError(f"A node named '{new_name}' already exists in folder: {node.getParent()}")

        node.setName(new_name)
        if (config.TEST_MODE): print(f"Node renamed to: {node.getName()}")
        if (config.TEST_MODE): print(f"====== End StorageManager.Rename ======\n")

    # The position of the node is moved to the folder's children list.
    # RQ4(b): the user can move any file or folder freely -- Favorites no
    # longer holds shared file references (favoriting is just a flag now, see
    # ToggleFavorite), so every folder (including Favorites and Trash) is a
    # plain folder as far as Move is concerned.
    # If the node being moved currently sits in Trash, this doubles as
    # "restore": its deletedAt stamp is cleared so PurgeExpiredTrash no
    # longer considers it for purging.
    def Move(self, node: StorageNode, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Move ======")
        if (config.TEST_MODE): print(f"Moving node: {node} to folder: {folder}...")

        if (config.TEST_MODE): print(f"node: {node}\n, name: {node.getName()}\n, parent: {node.getParent()}")
        if (config.TEST_MODE): print(f"folder: {folder}\n, name: {folder.getName()}\n, children: {folder.children}\n, parent: {folder.getParent()}")

        wasInTrash = node.getParent() is self.trash

        if node.getParent():
            if (config.TEST_MODE): print(f"Removing node: {node} from its current parent: {node.getParent()}...")
            node.getParent().Remove(node)
        else:
            if (config.TEST_MODE): print(f"Node: {node} has no current parent")
        
        node.setParent(folder)
        folder.children.append(node)

        if wasInTrash:
            if (config.TEST_MODE): print(f"Node: {node} restored out of Trash; clearing its deletedAt stamp")
            node.setDeletedAt(None)

        if (config.TEST_MODE): print(f"Node moved: {node} to folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.Move ======\n")
        return node

    # RQ: The root, Favorites, Input, Output, and Trash folders cannot be deleted.
    # RQ6/RQ13: deleting anything else is a *soft* delete -- the node (and,
    # if it's a folder, everything inside it, which just moves along with
    # it) is relocated into Trash with a deletedAt stamp, instead of being
    # erased immediately. Deleting a node that is already in Trash means
    # "empty this from Trash now" -- it skips the grace period and erases
    # it for real right away.
    def Delete(self, node: StorageNode): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Delete ======")
        if (config.TEST_MODE): print(f"Deleting node: {node}...")

        match node:
            case self.root | self.favorites | self.input | self.output | self.trash:
                if (config.TEST_MODE): print(f"Cannot delete node: {node}, as it is a protected folder")
                if (config.TEST_MODE): print(f"====== End StorageManager.Delete ======\n")
                return
            case _ if node.getParent() is self.trash:
                if (config.TEST_MODE): print(f"Node: {node} is already in Trash; erasing it immediately")
                self._hardDelete(node)
                if (config.TEST_MODE): print(f"====== End StorageManager.Delete ======\n")
                return
            case _:
                if (config.TEST_MODE): print(f"Node: {node}\n, name: {node.getName()}\n, parent: {node.getParent()}")
                if node.getParent():
                    if (config.TEST_MODE): print(f"Removing node: {node} from its current parent: {node.getParent()}...")
                    node.getParent().Remove(node)

                node.setDeletedAt(datetime.now(timezone.utc).isoformat())
                node.setParent(self.trash)
                self.trash.children.append(node)

                if (config.TEST_MODE): print(f"Node: {node} soft-deleted into Trash at: {node.getDeletedAt()}")
                if (config.TEST_MODE): print(f"====== End StorageManager.Delete ======\n")

    # Permanently erases node (recursing into its children, if it's a
    # Folder) -- the behavior Delete() used to apply immediately, now only
    # used for already-trashed nodes (via Delete) and expired ones (via
    # PurgeExpiredTrash).
    def _hardDelete(self, node: StorageNode):
        if (config.TEST_MODE): print(f"\n====== StorageManager._hardDelete ======")
        if (config.TEST_MODE): print(f"Erasing node: {node}...")

        if node.getParent():
            node.getParent().Remove(node)
        node.setParent(None)

        if isinstance(node, Folder):
            for child in node.children[:]:
                self._hardDelete(child)

        node.delete() if hasattr(node, "delete") else None
        if (config.TEST_MODE): print(f"Erased node: {node}")
        if (config.TEST_MODE): print(f"====== End StorageManager._hardDelete ======\n")

    # RQ6/RQ13: erases every Trash entry whose grace period (GRACE_PERIOD,
    # 30 days) has elapsed. Not a background job -- callers invoke this
    # explicitly whenever they want expired entries swept out. `now`
    # defaults to the real current time but can be passed in (as a
    # timezone-aware datetime, to match the UTC stamps Delete() writes) to
    # test grace-period expiry without waiting.
    def PurgeExpiredTrash(self, now: datetime = None) -> list[StorageNode]:
        if (config.TEST_MODE): print(f"\n====== StorageManager.PurgeExpiredTrash ======")
        now = now if now is not None else datetime.now(timezone.utc)

        purged = []
        for node in self.trash.children[:]:
            deletedAt = node.getDeletedAt()
            if deletedAt is None:
                continue
            if now - datetime.fromisoformat(deletedAt) >= self.GRACE_PERIOD:
                if (config.TEST_MODE): print(f"Purging expired Trash entry: {node}")
                self._hardDelete(node)
                purged.append(node)

        if (config.TEST_MODE): print(f"====== End StorageManager.PurgeExpiredTrash ======\n")
        return purged

    # RQ4(c)/RQ4(f): favoriting a File or Folder is just a boolean flag --
    # it does not relocate the node into a "Favorites" folder (there isn't
    # one anymore functionally; Favorites above is just a plain folder the
    # user can use like any other), and favoriting a Folder does not cascade
    # to its contents.
    def ToggleFavorite(self, node: StorageNode): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.ToggleFavorite ======")
        if (config.TEST_MODE): print(f"Toggling favorite status for node: {node}")
        if not isinstance(node, (File, Folder)):
            if (config.TEST_MODE): print(f"Cannot toggle favorite for node: {node}")
            if (config.TEST_MODE): print(f"====== End StorageManager.ToggleFavorite ======\n")
            return

        node.setFavorite(not node.getFavorite())
        if (config.TEST_MODE): print(f"Node: {node}\n, name: {node.getName()}\n, favorite: {node.getFavorite()}")
        if (config.TEST_MODE): print(f"====== End StorageManager.ToggleFavorite ======\n")

    def DuplicateFile(self, file: File, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.DuplicateFile ======")
        if (config.TEST_MODE): print(f"Duplicating file: {file} to folder: {folder}")

        duplicate = file.deepCopy()
        duplicate = self.remakeDuplicateName(duplicate, folder)

        self.Add(duplicate, folder)
        if (config.TEST_MODE): print(f"File duplicated: {duplicate} to folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.DuplicateFile ======\n")

    # RQ5(files, case 2): creates a new File in folder. With no name given,
    # it's auto-named "untitled(N)" (the next free number in that folder)
    # instead of requiring the caller to pick one upfront.
    def CreateFile(self, folder: Folder, name: str = None) -> File:
        if (config.TEST_MODE): print(f"\n====== StorageManager.CreateFile ======")
        file = File()
        file.setName(name if name else self._nextUntitledName(folder))
        file.setCreationTime(datetime.now(timezone.utc).isoformat())

        self.Add(file, folder)
        if (config.TEST_MODE): print(f"File created: {file} in folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.CreateFile ======\n")
        return file

    # RQ5(folders): creates a new Folder in parentFolder, stamped with its
    # creation time (so Sorter can order folders by date_created, RQ3).
    def CreateFolder(self, parentFolder: Folder, name: str) -> Folder:
        if (config.TEST_MODE): print(f"\n====== StorageManager.CreateFolder ======")
        folder = Folder()
        folder.setName(name)
        folder.setDateCreated(datetime.now(timezone.utc).isoformat())

        self.Add(folder, parentFolder)
        if (config.TEST_MODE): print(f"Folder created: {folder} in folder: {parentFolder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.CreateFolder ======\n")
        return folder

    # PRIVATE - Helper functions

    # The next unused "untitled(N)" name in folder, starting at 1.
    def _nextUntitledName(self, folder: Folder) -> str:
        existing_names = {child.getName() for child in folder.getChildren()}
        counter = 1
        name = f"untitled({counter})"
        while name in existing_names:
            counter += 1
            name = f"untitled({counter})"
        return name

    # Uniqueness property of file names
    def remakeDuplicateName(self, file: File, folder: Folder):
        duplicate = file
        original_name = duplicate.getName()
        existing_names = {child.getName() for child in folder.getChildren()}

        if original_name not in existing_names:
            print(f"No duplicate name found for: {original_name} in folder: {folder}")
            return duplicate

        if (config.TEST_MODE): print(f"Duplicate name found: {original_name} in folder: {folder}")

        # If the name already ends with "_copyN", pull out N and resume counting
        # from N + 1 instead of stacking another "_copy1" onto an already-copied name.
        match = re.match(r"^(.*)_copy(\d+)$", original_name)
        if match:
            base_name, counter = match.group(1), int(match.group(2)) + 1
        else:
            base_name, counter = original_name, 1

        new_name = f"{base_name}_copy{counter}"
        while new_name in existing_names:
            counter += 1
            new_name = f"{base_name}_copy{counter}"

        duplicate.setName(new_name)
        return duplicate
    
