from ctypes import *

msvcrt = cdll.msvcrt  # uses cdecl calling convention to export our 'printf'
message_string = "Hello World!\n"
msvcrt.printf("Testing: {}".format(message_string))
