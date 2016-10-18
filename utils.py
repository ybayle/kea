
import os
import sys
from datetime import datetime

VERBOSE = True

COLOR = {
    "HOUR" : "\033[96m",
    "HEADER" : "\033[95m",
    "OKBLUE" : "\033[94m",
    "OKGREEN" : "\033[92m",
    "WARNING" : "\033[93m",
    "ERROR" : "\033[91m",
    "FILE" : "\033[37m",
    "ENDC" : "\033[0m",
    "BOLD" : "\033[1m",
    "UNDERLINE" : "\033[4m"
}

def curTime():
    return COLOR["HOUR"] + datetime.now().time().strftime("%Hh%Mm%Ss") + " " + COLOR["ENDC"]

def print_error(msg):
    """Description of print_error

    Print error message and exit program
    """
    disp_msg = "\n" + curTime() + COLOR["BOLD"] + COLOR["ERROR"] + "ERROR:\n" 
    disp_msg = disp_msg + str(msg) + "\nProgram stopped" + COLOR["ENDC"]
    print(disp_msg)
    sys.exit()

def print_info(msg):
    """Description of print_info

    Print info message
    """
    if VERBOSE:
        print(curTime() + COLOR["OKBLUE"] + str(msg) + COLOR["ENDC"])

def print_warning(msg):
    """Description of print_warning

    Print warning message
    """
    if VERBOSE:
        print(curTime() + COLOR["WARNING"] + str(msg) + COLOR["ENDC"])

def print_success(msg):
    """Description of print_success

    Print success message
    """
    if VERBOSE:
        print(curTime() + COLOR["BOLD"] + COLOR["OKGREEN"] + msg + COLOR["ENDC"])

def print_msg(msg):
    """Description of print_msg

    Print default message
    """
    if VERBOSE:
        print(COLOR["HEADER"] + msg + COLOR["ENDC"])

def print_file(fileName):
    if os.path.isfile(fileName):
        printInfo(fileName + ":")
        print(COLOR["FILE"])
        with open(fileName, 'r') as fn:
            for line in fn:
                print(line[:-1])
        print(COLOR["ENDC"])
    else:
        printWarning("File not found: " + fileName)

def abs_path_dir(dir_name):
    """Description of abs_path_dir

    Check validity of directory and return absolute path
    Otherwise raise error and end programm
    """
    if not os.path.isfile(dir_name) and os.path.exists(dir_name):
        return os.path.abspath(dir_name)
    else:
        print_error("Invalid directory name: " + dir_name)

def abs_path_file(filename):
    """Description of abs_path_file

    Check validity of file name and return absolute path of it
    Otherwise raise error and end programm
    """
    if os.path.isfile(filename) and os.path.exists(filename):
        return os.path.abspath(filename)
    else:
        print_error("Invalid file name: " + filename)
