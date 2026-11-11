'''
main.py

'''
import PageManager
import StorageManager
import StorageNode

import argparse
import config


def main():
    parser = argparse.ArgumentParser(description="Journaling Program")

    args = parser.parse_args()

    # Initialization of PageManager and StorageManager
    if config.TEST_MODE: print("Initializing Program...")

    sM = StorageManager.StorageManager()
    pM = PageManager.PageManager(sM)

    if config.TEST_MODE: print("Program Initialized.")


if __name__ == "__main__":
    main()