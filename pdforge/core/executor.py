"""Bounded process supervisor for trusted adapters, never agent shell strings.
This is not a filesystem sandbox. Public native dispatch remains disabled.
"""
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time
import resource


def supervise(argv, cwd, wall_s, cpu_s, max_log_bytes=65536):
    if not isinstance(argv,list) or not argv or not all(isinstance(a,str) for a in argv):
        raise ValueError('Argument array required')
    if min(wall_s,cpu_s,max_log_bytes)<=0: raise ValueError('Positive limits required')
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU,(max(1,int(cpu_s)),max(1,int(cpu_s))))
        resource.setrlimit(resource.RLIMIT_FSIZE,(max_log_bytes,max_log_bytes))
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    p = subprocess.Popen(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=limits,
                         env={'PATH':'/usr/bin:/bin','LANG':'C','HOME':str(Path(cwd))})
    s = selectors.DefaultSelector()
    s.register(p.stdout,selectors.EVENT_READ)
    output = bytearray()
    timeout = False
    try:
        while s.get_map():
            if time.monotonic()-start > wall_s:
                timeout = True
                break
            for key,_ in s.select(.02):
                data = os.read(key.fileobj.fileno(),8192)
                if not data: s.unregister(key.fileobj)
                else: output.extend(data[:max(0,max_log_bytes-len(output))])
        if not timeout:
            try: p.wait(timeout=max(.01,wall_s-(time.monotonic()-start)))
            except subprocess.TimeoutExpired: timeout = True
    finally:
        # Terminate all descendants even when parent exited successfully.
        try: os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        p.wait()
        p.stdout.close()
        s.close()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {'status':'timeout' if timeout else 'completed' if p.returncode==0 else 'failed',
            'exit_code':p.returncode,'wall_s':time.monotonic()-start,
            'cpu_s':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'log':output.decode(errors='replace'),'log_truncated':len(output)>=max_log_bytes}
