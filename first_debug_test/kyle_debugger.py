from ctypes import *
from kyle_debugger_defs import *

kernel32 = windll.kernel32


class Debugger():

    def __init__(self):
        self.h_process = None
        self.pid = None
        self.debugger_active = False
        self.h_thread = None
        self.context = None
        self.exception = None
        self.exception_address = None

    def load(self, path_to_exe):

        # dwCreation flag determines how to create the process
        # set creation_flags = CREATE_NEW_CONSOLE if you want
        # to see the calculator GUI
        creation_flags = DEBUG_PROCESS

        # instantiate the structs
        startupinfo = STARTUPINFO()
        process_information = PROCESS_INFORMATION()

        # The following two options allow the started process
        # to be shown as a separate window. This also illustrates
        # how different settings in the STARTUPINFO struct can affect
        # the debugger.
        startupinfo.dwFlags = 0x1
        startupinfo.wShowWindow = 0x0

        # We then initialize the cb variable in the STARTUPINFO struct
        # which is just the size of the struct itself
        startupinfo.cb = sizeof(startupinfo)

        if kernel32.CreateProcessA(path_to_exe,
                                   None,
                                   None,
                                   None,
                                   None,
                                   creation_flags,
                                   None,
                                   None,
                                   byref(startupinfo),
                                   byref(process_information)):

            print "[*] We have successfully launched the process!"
            print "[*] The PID is: %d" % process_information.dwProcessId
            self.pid = process_information.dwProcessId
            # Obtain a handle to the newly created process and store it for future use
            self.h_process = self.open_process(process_information.dwProcessId)
            self.debugger_active = True
        else:
            print "[*] Error with error code %d." % kernel32.GetLastError()

    def open_process(self, pid):
        # OpenProcess() is exported via kernel32.dll. For debugging, param must be set to
        # PROCESS_ALL_ACESS. The 2nd param - corresponding to bInherit, will always be False
        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        return h_process

    def attach(self, pid):
        # Call the above, and store for use
        self.h_process = self.open_process(pid)

        # We attempt to attach to the process - pass the PID
        # if this fails we exit the call
        if kernel32.DebugActiveProcess(pid):
            self.debugger_active = True
            self.pid = int(pid)
        else:
            print "[*] Unable to attach to the process."

    def run(self):

        # Now we have to poll the debugger for
        # debugging events           
        while self.debugger_active:
            self.get_debug_event()

    def get_debug_event(self):

        debug_event = DEBUG_EVENT()
        continue_status = DBG_CONTINUE
        # After control control to debug proc is released to us, events are trapped in a loop
        # using WaitForDebugEvent
        if kernel32.WaitForDebugEvent(byref(debug_event), INFINITE):  # 2nd param is the time to return
            # Obtain the thread & context info...
            # update self h_thread val from None and pass to get_thread_context
            self.h_thread = self.open_thread(debug_event.dwThreadId)
            self.context = self.get_thread_context(self.h_thread)
            print "Event Code: %d. Thread ID %d" \
                  % (debug_event.dwDebugEventCode, debug_event.dwThreadId)
            # If event is exception, examine it further...
            if debug_event.dwDebugEventCode == EXCEPTION_DEBUG_EVENT:
                # Obtain the exception code
                exception = debug_event.u.Exception.ExceptionRecord.ExceptionCode
                self.exception_address = debug_event.u.Exception.ExceptionRecord.ExceptionAddress
                if exception == EXCEPTION_ACCESS_VIOLATION:
                    print "Access violation detected."
                    # If breakpoint detected, call an internal handler
                elif exception == EXCEPTION_BREAKPOINT:
                    continue_status = self.exception_handler_breakpoint()
                elif exception == EXCEPTION_GUARD_PAGE:
                    print "Guard page access detected."
                elif exception == EXCEPTION_SINGLE_STEP:
                    print "Single stepping."

            kernel32.ContinueDebugEvent(debug_event.dwProcessId,  # the DEBUG_EVENT() params are initialized when
                                            debug_event.dwThreadId,  # the debugger catches an event
                                            continue_status)  # keep executing or keep processing exception -
                                                              # via DBG_EXCEPTION_NOT_HANDLED

    def exception_handler_breakpoint(self):

        print """[*] Inside the breakpoint handler.
                Exception address: 0x%08x
        """ % self.exception_address
        return DBG_CONTINUE

    def detach(self):  # DebugActiveProcessStop only takes the PID we wish to detach from as a param

        if kernel32.DebugActiveProcessStop(self.pid):
            print "[*] Finished debugging. Exiting..."
            return True
        else:
            print "[!] There was an error"
            return False

    def open_thread(self, thread_id):
        # similar to OpenProcess, except we pass the TID instead of PID
        h_thread = kernel32.OpenThread(THREAD_ALL_ACCESS, None, thread_id)

        if h_thread is not None:
            return h_thread
        else:
            print "[*] Could not obtain a valid thread handle."
            return False

    def enumerate_threads(self):

        thread_entry = THREADENTRY32()
        thread_list = []
        # This is also exported from kernel32.dll. Helps us examine procs, threads, modules, heaps
        # owned by a process. In this case, TH32_SNAPTHREAD will gather ALL threads currently registered
        # in the snapshot - value of 0x00000004, 2nd param corresponds to PID of interest. However,
        # it's NOT used by TH32_SNAPTHREAD so we need to determine if a thread belongs to our process
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, self.pid)

        if snapshot is not None:

            # You have to set the size of the struct
            # or the call will fail
            thread_entry.dwSize = sizeof(thread_entry)
            # Then, we can begin the enum. The fields we're interested in are: dwSize (above), th32OwnerProcessID,
            # and th32ThreadID - which is the TID of the thread we're examining
            success = kernel32.Thread32First(snapshot, byref(thread_entry))
            while success:
                # This performs the comparison we need to determine if the owning process is the one
                # we're interested in
                if thread_entry.th32OwnerProcessID == self.pid:
                    thread_list.append(thread_entry.th32ThreadID)
                # same format as Thread32First, for any subsequent threads...if multi-threaded
                success = kernel32.Thread32Next(snapshot, byref(thread_entry))
            # No need to explain this call, it closes handles
            # so that we don't leak them.
            kernel32.CloseHandle(snapshot)
            return thread_list
        else:
            return False

    def get_thread_context(self, thread_id):
        # Modified for platform compatibility - added class structs in defs
        context = CONTEXT64()
        context.ContextFlags = CONTEXT_FULL | CONTEXT_DEBUG_REGISTERS
        # Obtain a handle to the thread
        h_thread = self.open_thread(thread_id)
        # GetThreadContext - 1st param we pass is the handle returned from OpenThread(). 2nd param
        # points to the CONTEXT (in this case, my modded CONTEXT64) struct
        if kernel32.GetThreadContext(h_thread, byref(context)):
            kernel32.CloseHandle(h_thread)
            return context
        else:
            return False
