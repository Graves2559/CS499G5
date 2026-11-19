'''
Item.py

Defines the Item class used in the journaling program.

'''

import config

class Item:
    def __init__(self, content: str):
        self.content = content
        self.position = None  # Position will be set when the item is added to a file.
        self.id = None  # Unique identifier for the item, can be set when the item is added to a file.
        self.timestamp = None  # Timestamp will be set when the item is added to a file.

    def get_content(self) -> str:
        print(f"\nGetting content: {self.content}")
        return self.content

    def get_position(self) -> int:
        print(f"\nGetting position: {self.position}")
        return self.position

    def get_id(self) -> int:
        print(f"\nGetting id: {self.id}")
        return self.id

    def get_timestamp(self) -> str:
        print(f"\nGetting timestamp: {self.timestamp}")
        return self.timestamp

    def set_content(self, content: str):
        if (config.TEST_MODE): print(f"\nSetting content from {self.content} to {content}")
        self.content = content
        if (config.TEST_MODE): print(f"Content set to {self.content}")
    
    def set_position(self, position: int):
        if (config.TEST_MODE): print(f"\nSetting position from {self.position} to {position}")
        self.position = position
        if (config.TEST_MODE): print(f"Position set to {self.position}")

    def set_id(self, id: int):
        if (config.TEST_MODE): print(f"\nSetting id from {self.id} to {id}")
        self.id = id
        if (config.TEST_MODE): print(f"Id set to {self.id}")

    def set_timestamp(self, timestamp: str):
        if (config.TEST_MODE): print(f"\nSetting timestamp from {self.timestamp} to {timestamp}")
        self.timestamp = timestamp
        if (config.TEST_MODE): print(f"Timestamp set to {self.timestamp}")