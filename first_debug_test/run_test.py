import kyle_debugger  # import the logic and start a process

debugger = kyle_debugger.Debugger()
#debugger.load("C:\\Windows\\System32\\calc.exe")
pid = raw_input("Enter the PID of the process to attach to => ")
debugger.attach(int(pid)) # of course we need to convert raw_inp str
debugger.detach() # then call the exit func

