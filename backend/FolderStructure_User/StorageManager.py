'''
StorageManager.py

'''
import re
import config
from StorageNode import StorageNode, File, Folder
from Sorter import Sorter, SortMetric

class StorageManager:
    def __init__(self): 
        self.root: Folder = Folder()    # The repository root directory itself (the entry point into the repository)
        self.favorites: Folder = Folder()
        self.input: Folder = Folder()
        self.output: Folder = Folder()

        self.root.setName("Root")
        self.favorites.setName("Favorites")  # No folders can be added in here. Duplicate files allowed.
        self.input.setName("Input")          # Plain folder: files and subfolders can be added/moved freely.
        self.output.setName("Output")        # Plain folder: files and subfolders can be added/moved freely.

        self.Add(self.favorites, self.root)
        self.Add(self.input, self.root)
        self.Add(self.output, self.root)

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

    # Adds file or folder to a folder
    # RQ: For the Favorites folder, only files can be added inside.
    # Input and Output are plain folders: files and subfolders can be added freely.
    def Add(self, node: StorageNode, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Add ======")
        if (config.TEST_MODE): print(f"Adding node: {node} to folder: {folder}...")

        if folder == self.favorites and not isinstance(node, File):
            if (config.TEST_MODE): print(f"Cannot add non-file node: {node} to Favorites folder")
            if (config.TEST_MODE): print(f"====== End StorageManager.Add ======\n")
            return

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
        node.setName(new_name)
        if (config.TEST_MODE): print(f"Node renamed to: {node.getName()}")
        if (config.TEST_MODE): print(f"====== End StorageManager.Rename ======\n")

    # The position of the node is moved to the folder's children list.
    # RQ: Nothing can be moved from the Favorites folder - it can only have a copy made via duplication to another folder
    # Returns the node that actually ended up in `folder`: either `node`
    # itself (a genuine move happened) or a new deep copy (the original
    # stayed in place, per the RQ above) -- None if the move was refused
    # outright. Callers (e.g. e2e.move) use this to know which object to
    # persist, and how.
    def Move(self, node: StorageNode, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Move ======")
        if (config.TEST_MODE): print(f"Moving node: {node} to folder: {folder}...")

        # Favorites is a SECOND reference to the same file object (see
        # ToggleFavorite), not its real folder -- it can't actually leave.
        # Duplicate instead and place the duplicate in `folder`, leaving the
        # original (and its Favorites membership) untouched. Input and
        # Output are plain folders, so nodes move out of them freely.
        if node in self.favorites.children:
            if (config.TEST_MODE): print(f"Cannot move node: {node} out of Favorites folder")
            if (config.TEST_MODE): print(f"Duplicating node into some folder...")
            deepCopy = node.deepCopy()
            deepCopy = self.remakeDuplicateName(deepCopy, folder)  # avoid a silent name collision in folder
            if (config.TEST_MODE): print(f"Deep copy created: {deepCopy}")

            if (config.TEST_MODE): print(f"Adding deep copy: {deepCopy} to folder: {folder}...")
            self.Add(deepCopy, folder)
            if (config.TEST_MODE): print(f"Deep copy added to folder: {folder}")
            if (config.TEST_MODE): print(f"====== End StorageManager.Move ======\n")
            return deepCopy

        if (config.TEST_MODE): print(f"node: {node}\n, name: {node.getName()}\n, parent: {node.getParent()}")
        if (config.TEST_MODE): print(f"folder: {folder}\n, name: {folder.getName()}\n, children: {folder.children}\n, parent: {folder.getParent()}")

        if node.getParent():
            if (config.TEST_MODE): print(f"Removing node: {node} from its current parent: {node.getParent()}...")
            node.getParent().Remove(node)
        else:
            if (config.TEST_MODE): print(f"Node: {node} has no current parent")
        
        node.setParent(folder)
        folder.children.append(node)
        if (config.TEST_MODE): print(f"Node moved: {node} to folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.Move ======\n")
        return node

    # RQ: The root, Favorites, Input, and Output folders cannot be deleted.
    def Delete(self, node: StorageNode): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.Delete ======")
        if (config.TEST_MODE): print(f"Deleting node: {node}...")

        # UNIT TEST TODO
        match node:
            case self.root | self.favorites | self.input | self.output:
                if (config.TEST_MODE): print(f"Cannot delete node: {node}, as it is a protected folder")
                if (config.TEST_MODE): print(f"====== End StorageManager.Delete ======\n")
                return
            case _:
                # Delete the node's dependencies
                if (config.TEST_MODE): print(f"Node: {node}\n, name: {node.getName()}\n, parent: {node.getParent()}")
                if node.getParent():
                    if (config.TEST_MODE): print(f"Removing node: {node} from its current parent: {node.getParent()}...")
                    node.getParent().Remove(node)
                    if (config.TEST_MODE): print(f"Node removed from its current parent: {node.getParent()}")
                node.setParent(None)

                if (isinstance(node, Folder)):
                    if (config.TEST_MODE): print(f"Deleting folder node's children...")
                    for child in node.children[:]:
                        self.Delete(child)
                    if (config.TEST_MODE): print(f"Deleted all of folder node's children")

                # Delete the node
                if (config.TEST_MODE): print(f"Deleting node: {node}...")
                node.delete() if hasattr(node, "delete") else None
                if (config.TEST_MODE): print(f"Deleted node: {node}")
                if (config.TEST_MODE): print(f"====== End StorageManager.Delete ======\n")

    def ToggleFavorite(self, file: File): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.ToggleFavorite ======")
        if (config.TEST_MODE): print(f"Toggling favorite status for file: {file}")
        if not isinstance(file, File):
            if (config.TEST_MODE): print(f"Cannot toggle favorite for non-file node: {file}")
            if (config.TEST_MODE): print(f"====== End StorageManager.ToggleFavorite ======\n")
            return

        if file in self.favorites.children and file.getFavorite():
            self.favorites.children.remove(file)
            file.setFavorite(False)
            if (config.TEST_MODE): print(f"File: {file}\n, name: {file.getName()}\n, parent: {file.getParent()}")
            if (config.TEST_MODE): print(f"File removed from Favorites folder: {file}")
        else:
            self.favorites.children.append(file)
            file.setFavorite(True)
            if (config.TEST_MODE): print(f"File: {file}\n, name: {file.getName()}\n, parent: {file.getParent()}")
            if (config.TEST_MODE): print(f"File added to Favorites folder: {file}")
        if (config.TEST_MODE): print(f"====== End StorageManager.ToggleFavorite ======\n")

    def DuplicateFile(self, file: File, folder: Folder): 
        if (config.TEST_MODE): print(f"\n====== StorageManager.DuplicateFile ======")
        if (config.TEST_MODE): print(f"Duplicating file: {file} to folder: {folder}")

        duplicate = file.deepCopy()
        duplicate = self.remakeDuplicateName(duplicate, folder)

        self.Add(duplicate, folder)
        if (config.TEST_MODE): print(f"File duplicated: {duplicate} to folder: {folder}")
        if (config.TEST_MODE): print(f"====== End StorageManager.DuplicateFile ======\n")

    # PRIVATE - Helper functions

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
    
