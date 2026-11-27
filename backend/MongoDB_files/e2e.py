
'''
e2e.py

End-to-end facade class for handling operations

'''

from DBManager import DBManager
import Database, documentDB, passwordDB
import argparse
import config

class E2e:
    def __init__(self, dBM: DBManager, args):
        if (config.TEST_MODE): print(f"\nInitializing E2e with arguments: {args}\n")
        self.DBManager = dBM    # Adapter/Manager for handling database operations
        self.args = args # Store the input file, output file, OCR, and E2E command-line arguments
        
        # args.l does not need an input file nor output file
        if self.args.l:
            self.list_all()

        # AND condition (for input file) for each elif
        if (not self.args.i):   # treat args.i as a container for files (likewise for args.o)
            print("No input file specified")
            return
        elif self.args.a:
            self.add_to_db()
        elif self.args.d:
            self.delete_from_db()
        elif self.args.e and self.args.o:
            self.edit_in_db()
        elif self.args.r:
            self.retrieve_from_db()
        else:   # default afterwards after a,d,e,and r options are checked
            self.process_with_AI()

    def add_to_db(self):
        # Implement the add operation using the DBManager and the provided arguments
        if self.args.psw:
            if (config.TEST_MODE): print(f"\nAdding to passwordDB: {self.args.i}...\n")
            # Implement the logic for handling password-related add operation
            pass

        else:
            if (config.TEST_MODE): print(f"\nAdding to documentDB: {self.args.i}...\n")
            # Implement the logic for handling file-related add operation
            self.DBManager.setDB(documentDB.DocumentDB())
            
            self.DBManager.add_to_db(self.args.i)  # Call the DBManager's add_to_database method with the provided file argument

    def delete_from_db(self):
        # Implement the delete operation using the DBManager and the provided arguments
        if self.args.psw:
            if (config.TEST_MODE): print(f"\nDeleting from passwordDB: {self.args.i}...\n")
            # Implement the logic for handling password-related delete operation
            pass
        else:
            if (config.TEST_MODE): print(f"\nDeleting from documentDB: {self.args.i}...\n")
            # Implement the logic for handling file-related delete operation
            self.DBManager.setDB(documentDB.DocumentDB())

            self.DBManager.delete_from_db(self.args.i)

    def edit_in_db(self):
        # Implement the edit/rename operation using the DBManager and the provided arguments
        if self.args.psw:
            if (config.TEST_MODE): print(f"\nEditing in passwordDB: {self.args.i}...\n")
            # Implement the logic for handling password-related edit operation
            pass
        else:
            if (config.TEST_MODE): print(f"\nEditing in documentDB: {self.args.i}...\n")
            # Implement the logic for handling file-related edit operation
            pass

    def retrieve_from_db(self):
        # Implement the get/retrieve operation using the DBManager and the provided arguments
        if self.args.psw:
            if (config.TEST_MODE): print(f"\nRetrieving from passwordDB: {self.args.i}...\n")
            # Implement the logic for handling password-related retrieve operation
            pass
        else:
            if (config.TEST_MODE): print(f"\nRetrieving from documentDB: {self.args.i}...\n")

            self.DBManager.setDB(documentDB.DocumentDB())
            result = self.DBManager.query_from_db(self.args.i)
            return result

    def list_all(self):
        if (self.args.ocr):
            if (config.TEST_MODE): print(f"\nListing the ocr...\n")
            pass
        if (self.args.llm):
            if (config.TEST_MODE): print(f"\nListing the llm...\n")
            pass

        if (not self.args.psw):
            # Implement the operation to list all entries using the DBManager and the provided arguments
            # Only use the **DOCUMENT** DB. Passwords are **NOT** meant to be displayed to the user nor admin.
            # If needed, access the password list through the password server.
            
            if (config.TEST_MODE): print(f"\nListing all from documentDB...\n")

            self.DBManager.setDB(documentDB.DocumentDB())
            results = self.DBManager.list_all_from_db()
            return results


    def process_with_AI(self):
        # Implement the operation to process input using AI and the provided arguments

        if (self.args.u and self.args.ocr):
            if (config.TEST_MODE): print(f"\nProcessing OCR...\n")
            # Implement the OCR processing logic here
            pass
            
        if (self.args.o and self.args.llm):
            if (config.TEST_MODE): print(f"\nProcessing LLM...\n")
            # Implement the LLM processing logic here
            pass

