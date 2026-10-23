
'''
main.py

TESTING MODE
During testing, the program will directly answer **FROM** the command execution of the program and the respective 
arguments within the command line/terminal.

# Turning on/off
To turn on test mode, simply reassign the parameter "TEST_MODE" within the "config.py" as True
When finished with testing, ensure that the parameter "TEST_MODE" is reassigned back to as False

# Purpose of testing mode
It will act as a simulator for the official mode. That is, the program  will provide the requests and such, as if
the request was sent by some client. To be clearer, the events will **NOT** be dependent on some real-world request.

For testing mode, these are the symbols to represent the operations:
    Primitives:
        --a : Add 
            f_dataConvert_Import (requires input file)
            f_assignOCR (requires OCR) [Must have --ocr as part of args]
        --d : Delete
            f_deleteDataDB (requires input file)
            f_deleteAllDataDB (requires input file)
        --e : Edit/rename
            f_adjustName (requires input file and output file)
    
    Files:
        --r : retrieve
            f_retrieveDataDB (requires input file)

    OCR:
        --u : Upload file
            f_uploadFileOCR (requires input file)

        --ocr : ocr specification ( **NOT** adding - it is an extension to specify that the program uses the OCR version)
    
    LLM:
        --o : Organize text
            f_organizeTextLLM (requires input file)

        --llm : LLM specification ( **NOT** adding - it is an extension to specify that the program uses the LLM version)

    Files and OCR:
        --l : list
            f_listData
            f_listOCR [Must have --ocr as part of args]

    Accompany ( **WITH** a file):
        --i = input file
        --o = output file

OFFICIAL MODE
During official mode, these should have happened:
1. The parameter "TEST_MODE" within the "config.py" is set to False
2. Per action (add, edit, delete, get, etc.), the backend server (this program) should state WITHIN itself that 
    the connection is successful.
    This means that the frontend should not display (per request) that the connection is successful to the user at all.
    It should instead state (step 3)
3. Per action (add, edit, delete, get, etc.), the backend server, once finished with its action,
    should provide a response to the frontend that the action/request is successful.
4. The program should not be interactive. It should receive some request, parse it, and then send the output
    and a successful response.

# Turning on/off
1. Initially, it will be executed via the terminal/command line, hearing for some request and such
2. Afterwards, it should be integrated into Docker, so that you only need to click a button on Docker to run it,
    instead of interacting with the terminal/command line.


# OPERATIONS
This program shall:

(A) Primitives:
1. Connect to the database
2. Add file(s) to the database
3. Change file(s) within the database
4. Delete file(s)within the database

(B) Extensions:
1. Make the files unique within the database, such that if the to-be-added file2 is the same identifer (name)
     as file 1 (within DB), then file2 will be marked with (k:1 to n). 
2. Connect to the login account. That is, have a password database (hashed)
3. Connect to the client and server program. That is, have a backend router (REST/HTTP API). Currently,
    we are using React as the frontend. Hence, we will use **FastAPI**, since it is dedicated for React. 
4. Connect to the WAN and LAN, with TLS encryption under HTTP (HTTPS). 


# IMPLEMENTATION
This program will use a facade pattern. That is, it will have a class that does some end-to-end operation/method 
from start to finish, using other objects (class instantiations) and input data to output something, according
to said end-to-end operation. The facade class will called "e2e.py".

This program will use the singleton pattern on the facade pattern, to enforce that there can be
no other root facades. 

We will have Manager classes to store the (if any) input files and (if any) intermediate output files.
Current Manager classes:
1. dBM DBManager       # This manager additionally acts as an Adapter (external-service-facing component) to the DB

We will have Resource classes to store the respective value(s) independently. These resource classes will
act as a container so that the Manager classes can act on them.
1. Data

'''

import argparse
import config 
from DBManager import DBManager
from e2e import E2e


def main():
    if (config.TEST_MODE): 
        print(f"\nParsing command-line arguments...\n")
        args = parseArgs()

    # DBManager(input file, output file)
    dBM = DBManager()
    e2e = E2e(dBM, args)


    pass

def parseArgs():
    parser = argparse.ArgumentParser(
        description="Display statistics for a branch in a git repository."
    )

    parser.add_argument("--i", nargs = "+") # input file : ≥1 files; if =1, then '?'
    parser.add_argument("--o", nargs = "+") # output file : ≥1 files; if =1, then '?'

    parser.add_argument(    # OCR is a version of operation that can be toggled on or off
        "--ocr",
        help="Specification of the OCR operation to perform",
        action="store_true"
    )
    parser.add_argument(    # llm is a version of operation that can be toggled on or off
        "--llm",
        help="Specification of the LLM operation to perform",
        action="store_true"
    )
    parser.add_argument(    # psw is a version of operation that can be toggled on or off. If off, then file.
                            # That is, file is the default storage if password operation is not used.
        "--psw",
        help="Specification of the password operation to perform",
        action="store_true"
    )
    group = parser.add_mutually_exclusive_group()   # Either e, d, a, l, r, c, or u
    group.add_argument( "--e",help="Specification of the edit/rename operation to perform", action="store_true")
    group.add_argument("--d", help="Specification of the delete operation to perform", action="store_true")
    group.add_argument("--a", help="Specification of the operation to perform: add (--a), delete (--d), or edit/rename (--e)", action="store_true")
    group.add_argument("--l", help="Specification of the list operation to perform", action="store_true")
    group.add_argument("--r", help="Specification of the retrieve operation to perform", action="store_true")
    group.add_argument("--c", help="Specification of the create operation to perform", action="store_true")
    group.add_argument("--u", help="Specification of the upload operation to perform", action="store_true")

    args = parser.parse_args()  # Different from ParseArgs() function name
    return args




if __name__ == "__main__":
    main()
