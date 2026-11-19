'''
DataManager.py

'''

from PageManager import PageManager
from StorageManager import StorageManager

# Bridge between facade (e2e) pattern and the lower-level implementations.
class DataManager():
    def __init__(self):
        self.pM = PageManager(self)
        self.sM = StorageManager(self)

    # ALL operations of the E2E.py for the PM AND SM SHOULD BE HANDLED THROUGH THIS CLASS


