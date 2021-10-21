import kyle_debugger
from kyle_debugger_defs import *

debugger = kyle_debugger.Debugger()
pid = raw_input("Enter the PID of the process to attach to: ")
debugger.attach(int(pid))
# lst = debugger.enumerate_threads()
# For each thread in the list we want to
# grab the value of each of the registers
# for thread in lst:
#     thread_context = debugger.get_thread_context(thread)
    # Now let's output the contents of some of the registers
    # print "[*] Dumping registers for thread ID: 0x%08x" % thread
    # print "[**] RIP: 0x%08x" % thread_context.Rip
    # print "[**] RSP: 0x%08x" % thread_context.Rsp
    # print "[**] RBP: 0x%08x" % thread_context.Rbp
    # print "[**] RAX: 0x%08x" % thread_context.Rax
    # print "[**] RBX: 0x%08x" % thread_context.Rbx
    # print "[**] RCX: 0x%08x" % thread_context.Rcx
    # print "[**] RDX: 0x%08x" % thread_context.Rdx
    # print "[*] END DUMP"
debugger.run()
debugger.detach()
