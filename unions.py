from ctypes import *


class BarleyAmount(Union):  # Unions can manipulate diff types of the same val
    _fields_ = [
        ("barley_long", c_long),
        ("barley_int", c_int),
        ("barley_char", c_char * 8),
    ]


value = raw_input("Enter the amount of barley to put into the beer vat => ")
my_barley = BarleyAmount(int(value))  # convert the str input
print "Barley amount as a long: %ld" % my_barley.barley_long  # access the vals
print "Barley amount as an int: %d" % my_barley.barley_long
print "Barley amount as a char/str: %s" % my_barley.barley_char  # output will be in ASCII representation of user input
