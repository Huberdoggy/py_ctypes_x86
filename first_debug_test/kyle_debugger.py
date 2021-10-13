from ctypes import *
from kyle_debugger_defs import *

kernel32 = windll.kernel32


class Debugger():
    def __init__(self):  # Init w/ flags off
        self.h_process = None
        self.pid = None
        self.debugger_active = False

    def load(self, path_to_exe):
        # dwCreation flag determines howto create the proc
        # set creation_flags = CREATE_NEW_CONSOLE to see the calc GUI
        creation_flags = DEBUG_PROCESS  # from our type defs
        # creation_flags = CREATE_NEW_CONSOLE

        # instantiate the structs...
        startup_information = STARTUPINFO()
        process_information = PROCESS_INFORMATION()

        # These opts allow the new process spawn separate window.
        # This helps us identify how various settings in StartupInfo struct
        # can affect the debugger
        startup_information.dwFlags = 0x1  # True
        startup_information.wShowWindow = 0x0  # False

        # Here, we init the cb var in StartupInfo struct
        # a.k.a => the size of the struct itself
        startup_information.cb = sizeof(startup_information)

        # set all params to Null except the those essential to create debug proc
        if kernel32.CreateProcessA(path_to_exe,
                                   None,
                                   None,
                                   None,
                                   None,
                                   creation_flags,
                                   None,
                                   None,
                                   byref(startup_information),
                                   byref(process_information)):
            print "[*] We have successfully launched the process!"
        else:
            print "[*] We have successfully launched the process!"
            print "[*] PID: {} ".format(process_information.dwProcessId)
        # Obtain a valid handle to the new created proc and store it
        self.h_process = self.open_process(process_information.dwProcessId)

    def open_process(self, pid):
        # Obtain correct access rights to perform debugging
        # Param for bInheritHandle will always be set False
        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, pid, False)
        return h_process

    def attach(self, pid):
        self.h_process = self.open_process(pid)
        # Attempt to attach to the proc, if fail, exit func call..
        if kernel32.DebugActiveProcess(pid):
            self.debugger_active = True
            self.pid = int(pid)
            self.run()
        else:
            print "[!] Unable to attach to the process."

    def run(self):
        # Poll the debugger for debugging events

        while self.debugger_active:
            self.get_debug_event()

    def get_debug_event(self):

        debug_event = DEBUG_EVENT()
        continue_status = DBG_CONTINUE

        if kernel32.WaitForDebugEvent(byref(debug_event), INFINITE):
            # We aren't going to build any event handlers yet, just resume the proc
            # raw_input("Press any key to continue... => ")
            # self.debugger_active = False  # flip flag off
            kernel32.ContinueDebugEvent(
                debug_event.dwProcessId,
                debug_event.dwThreadId,
                continue_status
            )

    def detach(self):

        if kernel32.DebugActiveProcessStop(self.pid):  # if successfully identified end
            print "[+] Finished debugging. Exiting.."
            return True
        else:
            print "[!] An error occurred."
            return False
