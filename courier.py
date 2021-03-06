"""
courier: an intelligent subprocessor
"""
import sys, subprocess, simplethread, cStringIO as StringIO

TERMINATOR = object()

class Courier:
    def __init__(self, storer=None):
        self.cwd = None
        if storer: self._store = storer
        self.dataq = simplethread.Queue()
    
    def cd(self, cwd):
        self.note('cd ' + cwd)
        self.cwd = cwd
        
    def run(self, *args, **kwargs):
        self.lastoutput = StringIO.StringIO()
        self.note(' '.join(args))
        p = subprocess.Popen(args, cwd=self.cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        simplethread.spawn(lambda: self._gobble(p.stderr))
        simplethread.spawn(lambda: self._gobble(p.stdout))
        simplethread.spawn(lambda: self._deathgobble(p.wait))
        
        if kwargs.get('bg'):
            simplethread.spawn(lambda: self._outputdata())
            return
        else:
            self._outputdata()
            return p.returncode
    
    def _outputdata(self):
        while 1:
            try:
                data = self.dataq.get(timeout=5)
            except simplethread.Empty:
                data = ''
            if data is TERMINATOR: break
            self.output(data)
        
        
    def _store(self, x):
        # gets overwritten by caller sometimes
        sys.stdout.write(x)
    
    def note(self, line):
        self._store('\033[1m$ ' + line + '\033[0m\n')
    
    def output(self, data):
        self.lastoutput.write(data)
        self._store(data)
    
    def _gobble(self, fileobj):
        [self.dataq.put(line) for line in iter(fileobj.readline, '')]
    
    def _deathgobble(self, func):
        func()
        self.dataq.put(TERMINATOR)

