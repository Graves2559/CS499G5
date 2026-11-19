'''
test_unit.py

The test_* is the syntax for pytest

'''

import pytest
from PageManager import PageManager
from Item import Item
from StorageManager import StorageManager
import StorageNode
from Sorter import SortMetric, Sorter

# PageManager Tests
def test_AddItem():
    sM = StorageManager()
    pM = PageManager(sM)
    file = StorageNode.File()
    item = Item("Test Item")
    
    pM.AddItem(file, item)

def test_DeleteItem():
    sM = StorageManager()
    pM = PageManager(sM)
    file = StorageNode.File()
    item = Item("Test Item")
    position = 0    # Note: This is a simulation. In the real world, the frontend will provide the correct position of the item to be deleted.
    
    pM.AddItem(file, item)
    pM.DeleteItem(file, item, position)

def test_EditItem():
    sM = StorageManager()
    pM = PageManager(sM)
    file = StorageNode.File()
    item = Item("Test Item")
    newStr = "Edited Item"
    
    pM.AddItem(file, item)
    pM.EditItem(file, item, newStr)

def test_CreatePage():
    sM = StorageManager()
    pM = PageManager(sM)
    file = StorageNode.File()
    folder = StorageNode.Folder()
    
    pM.CreatePage(file, folder)
    assert file in folder.children

## Edge Cases

def test_Delete_nonexistent_item():
    sM = StorageManager()
    pM = PageManager(sM)
    file = StorageNode.File()
    item = Item("Nonexistent Item")
    position = 0
    
    pM.DeleteItem(file, item, position)
    
    assert item not in file.ItemList



# StorageManager Tests

def test_AddNodeToFolder():
    sM = StorageManager()
    folder = StorageNode.Folder()
    file = StorageNode.File()
    
    sM.Add(file, folder)
    
    assert file in folder.children

def test_RenameNode():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Some Folder")
    file = StorageNode.File()
    file.setName("Original File")
    sM.Add(file, folder)
    
    new_name = "Renamed File"
    sM.Rename(file, new_name)
    
    assert file.getName() == new_name

def test_MoveFile():
    sM = StorageManager()
    folder1 = StorageNode.Folder()
    folder1.setName("Folder 1")
    folder2 = StorageNode.Folder()
    folder2.setName("Folder 2")
    
    file = StorageNode.File()
    sM.Add(file, folder1)
    
    sM.Move(file, folder2)
    
    assert file in folder2.children
    assert file not in folder1.children

def test_MoveFolder():
    sM = StorageManager()
    folder1 = StorageNode.Folder()
    folder1.setName("Folder 1")
    folder2 = StorageNode.Folder()
    folder2.setName("Folder 2")
    sM.Add(folder1, folder2)
    
    sM.Move(folder1, folder2)
    
    assert folder1 in folder2.children
    assert folder1 not in sM.root.children

def test_ToggleFavorite():
    # Should be able to toggle a file's favorite status
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    sM.ToggleFavorite(file)
    assert file in sM.favorites.children

    sM.ToggleFavorite(file)
    assert file not in sM.favorites.children

def test_DuplicateFile():
    # Should be able to duplicate a file to a folder
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)

    sM.DuplicateFile(file, folder)

    assert any(f.getName() == file.getName() for f in folder.children)
    assert file in sM.root.children

def test_DisplayAll():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    file.setName("File1")
    file1 = StorageNode.File()
    file1.setName("File0")
    sM.Add(file, sM.root)
    sM.Add(file1, sM.root)


    sM.DisplayAll(SortMetric.Filename)  # This should display all contents of the root folder without errors

def test_DisplayFolder():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    file.setName("File")
    file.setParent(folder)
    file1 = StorageNode.File()
    file1.setName("File1")
    file1.setParent(folder)

    sM.Add(file, folder)
    sM.Add(file1, folder)

    sM.DisplayFolder(folder, SortMetric.Filename)  # This should display all contents of the folder without errors

def test_DisplayFile():
    sM = StorageManager()
    file = StorageNode.File()
    file.setName("File")
    file.setParent(sM.root)
    sM.Add(file, sM.root)

    sM.DisplayFile(file)  # This should display the contents of the file without errors
## Edge cases
def test_DisplayAllFileName():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    file.setName("File1")
    file1 = StorageNode.File()
    file1.setName("File2")
    sM.Add(file, sM.root)
    sM.Add(file1, sM.root)

    sM.DisplayAll(SortMetric.Filename)  # This should display all contents of the root folder without errors
def test_DisplayAllDateModified():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    file.setName("File1")
    sM.Add(file, sM.root)
    file.setDateModified("2024-06-01")  # Set a date modified for sorting purposes

    sM.DisplayAll(SortMetric.DateModified)  # This should display all contents of the root folder without errors

def test_DisplayAllFavorite():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    file.setName("File1")
    file.setFavorite(True)  # Set the file as a favorite for sorting purposes
    sM.Add(file, sM.root)

    sM.DisplayAll(SortMetric.Favorite)  # This should display all contents of the root folder without errors


def test_MoveToRoot():
    sM = StorageManager()
    folder = StorageNode.Folder()
    folder.setName("Folder")
    file = StorageNode.File()
    file.setName("File1")
    sM.Add(file, folder)

    sM.Move(file, sM.root)

    assert file in sM.root.children
    assert file not in folder.children


def test_MoveFromInputFolder():
    # Input is a plain folder -- files should move out of it freely
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.input)

    sM.Move(file, sM.root)

    assert file not in sM.input.children
    assert file in sM.root.children

def test_MoveFromOutputFolder():
    # Output is a plain folder -- files should move out of it freely
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.output)

    sM.Move(file, sM.root)

    assert file not in sM.output.children
    assert file in sM.root.children

def test_MoveFromFavoritesFolder():
    # Should not be able to move files from the Favorites folder
    sM = StorageManager()
    favorites_folder = sM.favorites
    file = StorageNode.File()
    sM.Add(file, favorites_folder)

    sM.Move(file, sM.root)

    assert file in favorites_folder.children
    assert file not in sM.root.children

def test_AddFolderToInputFolder():
    # Should be able to add a folder to the Input folder
    sM = StorageManager()
    folder = StorageNode.Folder()

    sM.Add(folder, sM.input)

    assert folder in sM.input.children

def test_AddFolderToOutputFolder():
    # Should be able to add a folder to the Output folder
    sM = StorageManager()
    folder = StorageNode.Folder()

    sM.Add(folder, sM.output)

    assert folder in sM.output.children

def test_AddFileToFavoritesFolder():
    # Should be able to add a file to the Favorites folder
    sM = StorageManager()
    favorites_folder = sM.favorites
    file = StorageNode.File()
    
    sM.Add(file, favorites_folder)
    
    assert file in favorites_folder.children

def test_AddFolderToFavoritesFolder():
    # Should not be able to add a folder to the Favorites folder
    sM = StorageManager()
    favorites_folder = sM.favorites
    folder = StorageNode.Folder()
    
    sM.Add(folder, favorites_folder)
    
    assert folder not in favorites_folder.children

def test_MoveFromRoot():
    # Should be able to move files from the root folder
    sM = StorageManager()
    file = StorageNode.File()
    file.setName("File1")
    sM.Add(file, sM.root)

    folder = StorageNode.Folder()
    folder.setName("Folder1")
    sM.Add(folder, sM.root)

    sM.Move(file, folder)

    assert file in folder.children
    assert file not in sM.root.children

def test_DeleteProtectedFolders():
    # Should not be able to delete the root, Favorites, Input, or Output folders
    sM = StorageManager()
    
    sM.Delete(sM.root)
    sM.Delete(sM.favorites)
    sM.Delete(sM.input)
    sM.Delete(sM.output)

    assert sM.root is not None
    assert sM.favorites is not None
    assert sM.input is not None
    assert sM.output is not None


def test_ToggleFavoriteToFolder():
    # Should not be able to toggle a folder as favorite
    sM = StorageManager()
    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)

    sM.ToggleFavorite(folder)
    assert folder not in sM.favorites.children

def test_DuplicateFileToFavorites():
    # Should be able to duplicate a file to the Favorites folder
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    sM.DuplicateFile(file, sM.favorites)

    assert any(f.getName() == file.getName() for f in sM.favorites.children)
    assert file in sM.root.children

def test_DuplicateFileToRoot():
    # Should be able to duplicate a file to the root folder
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    sM.DuplicateFile(file, sM.root)

    assert any(f.getName() == file.getName() for f in sM.root.children)
    assert file in sM.root.children

def test_MoveFileFromInputFolder():
    # Moving a file out of the Input folder should succeed and really move it (Input is a plain folder)
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.input)

    destination = StorageNode.Folder()
    sM.Add(destination, sM.root)

    sM.Move(file, destination)

    assert file not in sM.input.children
    assert file in destination.children


# StorageNode

def test_FileGettersAndSetters():
    file = StorageNode.File()
    file.setEntryType(StorageNode.EntryType.W)
    file.setEntryNum(3)
    file.setData("Some journal entry text")
    file.setFavorite(True)

    assert file.getEntryType() == StorageNode.EntryType.W
    assert file.getEntryNum() == 3
    assert file.getData() == "Some journal entry text"
    assert file.getFavorite() == True

def test_FolderAddAndRemove():
    folder = StorageNode.Folder()
    file = StorageNode.File()

    folder.Add(file)
    assert file in folder.children
    assert file.getParent() == folder

    folder.Remove(file)
    assert file not in folder.children

def test_FileDeepCopy():
    file = StorageNode.File()
    file.setName("Original")
    file.setData("Some data")
    file.setEntryType(StorageNode.EntryType.D)
    file.setEntryNum(1)
    file.setFavorite(True)

    duplicate = file.deepCopy()

    assert duplicate is not file
    assert duplicate.getName() == file.getName()
    assert duplicate.getData() == file.getData()
    assert duplicate.getEntryType() == file.getEntryType()
    assert duplicate.getEntryNum() == file.getEntryNum()
    assert duplicate.getFavorite() == file.getFavorite()

## Edge Cases

def test_StorageNodeBaseClassRaises():
    # The base StorageNode class should not be used directly; its methods are meant to be overridden by subclasses
    node = StorageNode.StorageNode()

    with pytest.raises(BaseException):
        node.setName("New Name")
    with pytest.raises(BaseException):
        node.move(StorageNode.Folder())
    with pytest.raises(BaseException):
        node.delete()

def test_FileDeepCopy_DoesNotCopyItemList():
    # Documents current behavior: deepCopy does not carry over the file's ItemList
    file = StorageNode.File()
    file.ItemList.append(Item("Some Item"))

    duplicate = file.deepCopy()

    assert len(duplicate.ItemList) == 0

def test_FolderRemove_NonexistentNode():
    folder = StorageNode.Folder()
    file = StorageNode.File()  # never added to folder

    with pytest.raises(ValueError):
        folder.Remove(file)

# Item

def test_ItemGettersAndSetters():
    item = Item("Initial Content")
    item.set_content("Updated Content")
    item.set_position(2)
    item.set_id(42)
    item.set_timestamp(1234.5)

    assert item.get_content() == "Updated Content"
    assert item.get_position() == 2
    assert item.get_id() == 42
    assert item.get_timestamp() == 1234.5

## Edge Cases

def test_Item_DefaultValues():
    # A newly created Item should have no position, id, or timestamp assigned yet
    item = Item("Some Content")

    assert item.get_position() is None
    assert item.get_id() is None
    assert item.get_timestamp() is None

# Sorter

def test_SortByMetric_Filename():
    sorter = Sorter()
    file1 = StorageNode.File()
    file1.setName("zebra")
    file2 = StorageNode.File()
    file2.setName("apple")
    folder = StorageNode.Folder()
    folder.setName("a_folder")

    result = sorter.SortByMetric([file1, file2, folder], SortMetric.Filename)

    assert result == [folder, file2, file1]

def test_SortByMetric_DateModified():
    sorter = Sorter()
    file_old = StorageNode.File()
    file_old.setDateModified("2024-01-01")
    file_new = StorageNode.File()
    file_new.setDateModified("2024-06-01")
    folder = StorageNode.Folder()

    result = sorter.SortByMetric([file_new, folder, file_old], SortMetric.DateModified)

    assert result == [folder, file_old, file_new]

def test_SortByMetric_Favorite():
    sorter = Sorter()
    fav_file = StorageNode.File()
    fav_file.setFavorite(True)
    normal_file = StorageNode.File()
    normal_file.setFavorite(False)
    folder = StorageNode.Folder()

    result = sorter.SortByMetric([normal_file, folder, fav_file], SortMetric.Favorite)

    assert result == [folder, fav_file, normal_file]

## Edge cases

def test_SortByMetric_EmptyList():
    sorter = Sorter()

    result = sorter.SortByMetric([], SortMetric.Filename)

    assert result == []

def test_SortByMetric_InvalidMetricType():
    # Passing something that isn't a SortMetric should raise a TypeError, not silently misbehave
    sorter = Sorter()
    file = StorageNode.File()

    with pytest.raises(TypeError):
        sorter.SortByMetric([file], "not_a_metric")

def test_SortByMetric_DefaultsToFilenameWhenMetricNotProvided():
    sorter = Sorter()
    file1 = StorageNode.File()
    file1.setName("zebra")
    file2 = StorageNode.File()
    file2.setName("apple")

    result = sorter.SortByMetric([file1, file2])

    assert result == [file2, file1]

def test_SortByMetric_FoldersDoNotCrashOnFileOnlyMetrics():
    # Folders have no date_modified or favorite concept, but sorting by those metrics should still be safe
    sorter = Sorter()
    folder1 = StorageNode.Folder()
    folder2 = StorageNode.Folder()
    file = StorageNode.File()
    file.setDateModified("2024-01-01")
    file.setFavorite(True)

    date_result = sorter.SortByMetric([file, folder1, folder2], SortMetric.DateModified)
    favorite_result = sorter.SortByMetric([file, folder1, folder2], SortMetric.Favorite)

    assert date_result[-1] == file
    assert favorite_result[-1] == file