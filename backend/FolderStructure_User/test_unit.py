'''
test_unit.py

The test_* is the syntax for pytest

'''

import pytest
from datetime import datetime, timedelta, timezone

from FolderStructure_User.Manager.StorageManager import StorageManager
from FolderStructure_User.Resource import StorageNode
from FolderStructure_User.Transformer.Sorter import SortMetric, Sorter

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
    # Should be able to toggle a file's favorite status (RQ4: just a flag, no
    # relocation into a Favorites folder)
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    sM.ToggleFavorite(file)
    assert file.getFavorite() is True
    assert file in sM.root.children

    sM.ToggleFavorite(file)
    assert file.getFavorite() is False

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
    # Favorites is now a plain folder (RQ4) -- files move out of it freely,
    # the same as Input/Output.
    sM = StorageManager()
    favorites_folder = sM.favorites
    file = StorageNode.File()
    sM.Add(file, favorites_folder)

    sM.Move(file, sM.root)

    assert file not in favorites_folder.children
    assert file in sM.root.children

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
    # Favorites is now a plain folder (RQ4/RQ5.5) -- folders can be added
    # anywhere, including what used to be the file-only Favorites folder.
    sM = StorageManager()
    favorites_folder = sM.favorites
    folder = StorageNode.Folder()
    
    sM.Add(folder, favorites_folder)
    
    assert folder in favorites_folder.children

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
    # Should not be able to delete the root, Favorites, Input, Output, or Trash folders
    sM = StorageManager()
    
    sM.Delete(sM.root)
    sM.Delete(sM.favorites)
    sM.Delete(sM.input)
    sM.Delete(sM.output)
    sM.Delete(sM.trash)

    assert sM.root is not None
    assert sM.favorites is not None
    assert sM.input is not None
    assert sM.output is not None
    assert sM.trash is not None


def test_ToggleFavoriteToFolder():
    # RQ4(f): folders can be favorited directly, just like files
    sM = StorageManager()
    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)

    sM.ToggleFavorite(folder)
    assert folder.getFavorite() is True
    assert folder in sM.root.children  # favoriting does not relocate it

    sM.ToggleFavorite(folder)
    assert folder.getFavorite() is False

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
    file.setData("Some journal entry text")
    file.setFavorite(True)

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
    file.setFavorite(True)

    duplicate = file.deepCopy()

    assert duplicate is not file
    assert duplicate.getName() == file.getName()
    assert duplicate.getData() == file.getData()
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

def test_FolderRemove_NonexistentNode():
    folder = StorageNode.Folder()
    file = StorageNode.File()  # never added to folder

    with pytest.raises(ValueError):
        folder.Remove(file)

def test_FileUniqueIDIsGeneratedAndUnique():
    # Each File should get its own non-empty uniqueID on creation, distinct
    # from any other File's, since names are only unique within a folder.
    file1 = StorageNode.File()
    file2 = StorageNode.File()

    assert file1.getFileUniqueID()
    assert file2.getFileUniqueID()
    assert file1.getFileUniqueID() != file2.getFileUniqueID()

def test_FolderUniqueIDIsGeneratedAndUnique():
    folder1 = StorageNode.Folder()
    folder2 = StorageNode.Folder()

    assert folder1.getFolderUniqueID()
    assert folder2.getFolderUniqueID()
    assert folder1.getFolderUniqueID() != folder2.getFolderUniqueID()

def test_FileDeepCopy_GetsItsOwnUniqueID():
    # A duplicate is a distinct file, so it must not share the original's uniqueID
    file = StorageNode.File()

    duplicate = file.deepCopy()

    assert duplicate.getFileUniqueID() != file.getFileUniqueID()

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

def test_SortByMetric_DateModified_SortsFoldersByDateCreated():
    # RQ3: folders have no "modified" concept, so the DateModified metric
    # sorts them by their own date_created instead.
    sorter = Sorter()
    folder_old = StorageNode.Folder()
    folder_old.setDateCreated("2024-01-01")
    folder_new = StorageNode.Folder()
    folder_new.setDateCreated("2024-06-01")

    result = sorter.SortByMetric([folder_new, folder_old], SortMetric.DateModified)

    assert result == [folder_old, folder_new]

def test_SortByMetric_Favorite_SortsFavoritedFoldersFirst():
    # RQ4(f): folders can be favorited too, so the Favorite metric should
    # order them the same way it orders files.
    sorter = Sorter()
    fav_folder = StorageNode.Folder()
    fav_folder.setFavorite(True)
    normal_folder = StorageNode.Folder()

    result = sorter.SortByMetric([normal_folder, fav_folder], SortMetric.Favorite)

    assert result == [fav_folder, normal_folder]

# Unique naming (RQ5)

def test_Add_RaisesOnDuplicateName():
    sM = StorageManager()
    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)
    existing = StorageNode.File()
    existing.setName("report")
    sM.Add(existing, folder)

    duplicate = StorageNode.File()
    duplicate.setName("report")
    with pytest.raises(ValueError):
        sM.Add(duplicate, folder)

def test_Add_AllowsBlankNamedNodesToCoexist():
    # A blank/unset name isn't a "name" yet, so it's exempt from the
    # uniqueness check -- only CreateFile/CreateFolder's real names (and any
    # explicitly-set name) are enforced.
    sM = StorageManager()
    file1 = StorageNode.File()
    file2 = StorageNode.File()

    sM.Add(file1, sM.root)
    sM.Add(file2, sM.root)  # should not raise

    assert file1 in sM.root.children
    assert file2 in sM.root.children

def test_Rename_RaisesOnDuplicateName():
    sM = StorageManager()
    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)
    file1 = StorageNode.File()
    file1.setName("one")
    file2 = StorageNode.File()
    file2.setName("two")
    sM.Add(file1, folder)
    sM.Add(file2, folder)

    with pytest.raises(ValueError):
        sM.Rename(file2, "one")

# Creating files/folders (RQ5)

def test_CreateFile_AutoAssignsUntitledName():
    sM = StorageManager()
    file = sM.CreateFile(sM.root)

    assert file.getName() == "untitled(1)"
    assert file in sM.root.children
    assert file.getCreationTime() is not None

def test_CreateFile_IncrementsUntitledNumber():
    sM = StorageManager()
    first = sM.CreateFile(sM.root)
    second = sM.CreateFile(sM.root)

    assert first.getName() == "untitled(1)"
    assert second.getName() == "untitled(2)"

def test_CreateFile_WithExplicitName():
    sM = StorageManager()
    file = sM.CreateFile(sM.root, "notes")

    assert file.getName() == "notes"

def test_CreateFolder_SetsDateCreated():
    sM = StorageManager()
    folder = sM.CreateFolder(sM.root, "Subject")

    assert folder.getName() == "Subject"
    assert folder in sM.root.children
    assert folder.getDateCreated()

# Trash + grace period (RQ6/RQ13)

def test_Delete_SoftDeletesIntoTrash():
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)

    sM.Delete(file)

    assert file not in sM.root.children
    assert file in sM.trash.children
    assert file.getDeletedAt() is not None

def test_Delete_SoftDeletesFolderAndItsChildrenTogether():
    sM = StorageManager()
    folder = StorageNode.Folder()
    sM.Add(folder, sM.root)
    file = StorageNode.File()
    sM.Add(file, folder)

    sM.Delete(folder)

    assert folder in sM.trash.children
    assert file in folder.children  # the whole subtree moves as a unit

def test_Delete_AlreadyInTrash_ErasesImmediately():
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)
    sM.Delete(file)  # soft delete into Trash

    sM.Delete(file)  # deleting it again from Trash erases it for real

    assert file not in sM.trash.children

def test_Move_RestoringFromTrash_ClearsDeletedAt():
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)
    sM.Delete(file)
    assert file.getDeletedAt() is not None

    sM.Move(file, sM.root)

    assert file in sM.root.children
    assert file not in sM.trash.children
    assert file.getDeletedAt() is None

def test_PurgeExpiredTrash_RemovesEntriesPastGracePeriod():
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)
    sM.Delete(file)

    future = datetime.now(timezone.utc) + timedelta(days=31)
    purged = sM.PurgeExpiredTrash(now=future)

    assert purged == [file]
    assert file not in sM.trash.children

def test_PurgeExpiredTrash_KeepsEntriesWithinGracePeriod():
    sM = StorageManager()
    file = StorageNode.File()
    sM.Add(file, sM.root)
    sM.Delete(file)

    soon = datetime.now(timezone.utc) + timedelta(days=1)
    purged = sM.PurgeExpiredTrash(now=soon)

    assert purged == []
    assert file in sM.trash.children