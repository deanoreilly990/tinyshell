#!/usr/bin/env python
"""Usage:  tsh [options] [file]

Options:

    -h  --help      print this text and exit.

    -t  --test      perform some tests and exit.

    -v  --verbose   be verbose (mostly for debugging).

        --version   print version number and exit.
"""


import sys, os, os.path, glob, re
import datetime
import time
from pwd import getpwnam
import grp
import getpass
from os.path import expanduser

# The variables can be changed by the command line options:
VERBOSE = False

# Location of main configuration file:
CONFIG = '/bin/tinyshell/tsh.conf'

allowExec = []
allowSubShell = False

def pwd():
    home = expanduser("~")
    homeid = os.stat(home)
    gid = os.getgid()
    group_info = grp.getgrgid(gid)
    username = getpass.getuser()
    print 'UserID:',getpwnam(username).pw_uid
    print 'GroupID:',gid
    print 'GroupName:',group_info.gr_name
    print 'UserName :',getpwnam(username).pw_gecos
    print 'Inode:',homeid.st_ino

def date():
    t = time.ctime()
    print t
    thedatetime = time.strftime('%Y%m%d%H%M%S')
    print 'date',thedatetime

def readConfig():
    if os.access(CONFIG, os.R_OK):
        exec file(CONFIG) in globals()
    else:
        print "D-SHELL: Warning: Could not open `%s' for reading." % CONFIG

def lineSplit(line):
    line = line.strip()
    if not line or line[0]=='#':
        return '', ''
    tmp = line.split(None, 1)
    if tmp:
        return tmp[0], '' if len(tmp)==1 else tmp[1].strip()


def lock_down(cmd):
    allowed_arr = ['pw', 'dt', 'ud', 'ifc','exit','help']
    if cmd not in allowed_arr:
        return "'" + cmd +"'"
    else:
        return cmd
def help ():
    with open('/etc/issue.net', 'r') as fin:
        print fin.read()


class Shell:
    def __init__(self):
        self.alias = {}

    def do_alias(self, args):
        m = re.match(r"((\S+)='([^']+)')?$", args)
        if m:
            if m.group(2):
                self.alias[m.group(2)] = m.group(3)
            else:
                for kv in self.alias.iteritems():
                    print "alias %s='%s'" % kv
        else:
            print "D-SHELL: Usage: alias [name='value']"

    def do_unalias(self, args):
        m = re.match(r"(\S+)?$", args)
        if m:
            del self.alias[m.group(1)]
        else:
            print "D-SHELL: Usage: unalias name"

    def do_show_commands(self, args):
        if args == '':
            for kv in sorted(self.commands().items()):
                print "    %-15s %s" % kv
        else:
            print "D-SHELL: Usage: commands"


    def do_cd(self, args):
        """
        >>> s = Shell()
        >>> s.do_cd('/')
        >>> os.getcwd()
        '/'
        >>> s.do_cd('a b')
        tsh: Usage: cd [path]
        """
        m = re.match(r"(\S+)?$", args)
        if m:
            path = m.group(1) if m.group(1) else '~'
            try:
                os.chdir(os.path.expanduser(path))
            except:
                print "D-SHELL: cd: `%s' No such directory" % path
        else:
            print "D_SHELL: Usage: cd [path]"

    def execute_file(self, filename):
        if VERBOSE: print "D-SHELL: executing file `%s':" % filename
        for line in file(filename):
            self.execute(line)

    def execute(self, line):
        line = line.strip()
        cmd, args = lineSplit(line)

        #cmd = lock_down(cmd)
        # here I process the command to remove any args and then place a default in for incon -DOR
        if (cmd == 'pw'):
            args = ''
        if (cmd == 'ifc' and args == ''):
            args = 'eth0'
        if (cmd == 'dt'):
            date()
            return
        if (cmd == 'ud'):
            pwd()
            cmd = ""
            return
        if (cmd == 'help'):
            help()

        if not cmd:
            return
        f = self.rawExec
        if self.alias.has_key(cmd):
            alias = self.alias[cmd]
            line = alias + ' ' + args
            # print line
            # put in here a call to process all of my commands i.e. pwd ifconfig pw and date and then return it your way. Lock down rest then
            if lineSplit(alias)[0] != cmd:
                f = self.execute
        f(line)

    def rawExec(self, line):
        if VERBOSE: print "D-SHELL: executing: %s   " % line,
        cmd, args = lineSplit(line)
        funcname = "do_" + cmd
        if hasattr(self, funcname):
            if VERBOSE: print "(shell builtin)"
            func = getattr(self, funcname)
            try:
                func(args)
            except:
                print "D-SHELL: Error in line `%s'." % line
        elif cmd in allowExec:
            if VERBOSE: print "(os.spawn)"
            os.spawnvp(os.P_WAIT, cmd, line.split())
        else:
            if VERBOSE: print "(on subshell)"
            if allowSubShell:
                os.system(line)
            else:
                print "D-SHELL: `%s' Permission denied." % line

    def commands(self):
        """
        >>> s = Shell()
        >>> s.commands()['cd']
        'builtin'
        """
        res = {'exit': 'builtin'}
        for var in vars(self.__class__):
            if var.startswith('do_'):
                res[var[3:]] = 'builtin'
        for c in allowExec:
            res[c] = 'OS'
        for k, v in self.alias.items():
            tmp = "aliased '%s'" % v
            if res.has_key(k):
                res[k] += ", " + tmp
            else:
                res[k] = tmp
        return res

    def completions(self):
        res = self.commands()
        for f in glob.glob('*'):
            res[f] = True
        return res


def repl():
    try:
        import readline
        has_readline = True
    except ImportError:
        has_readline = False

    if has_readline:
        historyFile = os.path.expanduser('~/.tsh-history')
        if os.access(historyFile, os.W_OK):
            readline.read_history_file(historyFile)
            readline.set_history_length(100)
        else:
            ##print "D-SHELL: Could not open `%s' for writing." % historyFile
            try:
                file(historyFile, 'w').close()
                print "`%s' created." % historyFile
            except IOError:
               ## print "D-SHELL: Warning: Creating `%s' failed." % historyFile
                historyFile = None

        readline.parse_and_bind("tab: complete")

        def completer(prefix, index):
            try:
                return [w for w in words if w.startswith(prefix)][index]
            except IndexError:
                return None

        readline.set_completer(completer)

    shell = Shell()

    rcFile = os.path.expanduser('/bin/tinyshell/tshrc')
    if os.access(rcFile, os.R_OK):
        shell.execute_file(rcFile)

    while True:
        words = shell.completions()
        try:
            line = raw_input(' D-SHELL> ')
            cmd, args = lineSplit(line)
            line = lock_down(cmd) + ' ' + args
            if line.strip() == 'exit':
                break
            if has_readline and historyFile:
                readline.write_history_file(historyFile)
        except EOFError:
            print 'exit'
            break
        shell.execute(line)


def usage():
    print __doc__
    sys.exit(0)



if __name__ == '__main__':
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'htv',
                                   ['help', 'test', 'verbose', 'version'])
    except getopt.GetoptError:
        usage()

    for o, v in opts:
        if o in ('-h', '--help'): usage()
        if o in ('-t', '--test'): test()
        if o in ('-v', '--verbose'): VERBOSE = True
        if o == '--version':
            print 'tsh: version', __version__
            sys.exit(0)

    readConfig()
    if VERBOSE:
        print "tsh: allowExec = %r" % allowExec
        print "tsh: allowSubShell = %r" % allowSubShell

    if len(args) == 0:
        # Run interactively
        repl()
    elif len(args) == 1:
        # Interpret file
        filename = args[0]
        if os.access(filename, os.R_OK):
            Shell().execute_file(args[0])
        else:
            print "tsh: Could not open `%s' for reading." % filename
    else:
        usage()