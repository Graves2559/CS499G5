'''
Sorter.py

'''
from enum import Enum

from FolderStructure_User import config
from FolderStructure_User.Resource.StorageNode import StorageNode, File, Folder

class SortMetric(Enum):
    Filename = 1    # foldername (name) or filename(date)
    DateModified = 2
    Favorite = 3

class Sorter():
    def __init__(self):
        if (config.TEST_MODE): print("Initializing Sorter...")
        self.metric: SortMetric = SortMetric(1)
        if (config.TEST_MODE): print(f"Sorter initialized with metric: {self.metric}")

    # nodes: a collection of File and Folder objects to be sorted by the specified metric. 
    # The collection is usually through a StorageNode folder's children or similar structure.
    def SortByMetric(self, nodes: list[StorageNode], metric: SortMetric = None) -> list[StorageNode]:
        if metric is None:
            metric = SortMetric(1)

        if not isinstance(metric, SortMetric):
            raise TypeError(f"metric must be a SortMetric, got {type(metric).__name__}")

        self.metric = metric

        if (config.TEST_MODE): print(f"\nSorting nodes by metric: {self.metric}")
        if not nodes:
            print("No nodes to sort.")
            return nodes

        if self.metric == SortMetric.Filename:
            nodes.sort(key=lambda x: (not isinstance(x, Folder), x.getName()))
        elif self.metric == SortMetric.DateModified:
            # not isinstance(x, Folder) -> folders first
            # Files sort by date_modified; Folders have no "modified" concept
            # here, so they sort by their own date_created instead (RQ3).
            nodes.sort(key=lambda x: (not isinstance(x, Folder), x.getDateModified() if isinstance(x, File) else x.getDateCreated()))
        elif self.metric == SortMetric.Favorite:
            # not isinstance(x, Folder) -> folders first
            # Both Files and Folders can be favorited (RQ4), so both use their
            # own getFavorite() for the secondary sort key.
            nodes.sort(key=lambda x: (not isinstance(x, Folder), not x.getFavorite()))

        print(f"Nodes sorted by metric: {self.metric}")
        return nodes