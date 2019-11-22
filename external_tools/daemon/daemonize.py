"""
Based on code by Sander Marechal at http://www.jejik.com/files/examples/daemon.py
"""
from abc import ABCMeta
from abc import abstractmethod
import atexit
import errno
import os
import sys
import time
from signal import SIGTERM


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    __metaclass__ = ABCMeta

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Attempt to fork 1st time failed: {} ({})\n".format(e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("Attempt to fork 2nd time failed: {} ({})\n".format(e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+', 1)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "The daemon may already be running. The pidfile ({}) already exists.\n".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)

        # Start the daemon
        print ("Attempting to start {} as a daemon.".format(sys.argv[0]))
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "The daemon may not be running. The pidfile ({}) does not exist.\n".format(self.pidfile)
            sys.stderr.write(message)
            return  # not an error in a restart

        # Try killing the daemon process
        print ("Attempting to shutdown daemon process {}".format(pid))
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print (str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def status(self):
        """
        Get the status of the daemon
        """
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "The daemon may not be running. The pidfile ({}) does not exist.\n".format(self.pidfile)
            sys.stderr.write(message)
            sys.exit(1)

        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.EPERM:
                # EPERM clearly means there's a process to deny access to
                sys.stdout.write("The process with the PID {} is running but denied access.\n".format(pid))
            else:
                sys.stderr.write("There is not a process with the PID {} specified in {}\n".format(pid, self.pidfile))
                sys.exit(1)

        sys.stdout.write("The process with the PID {} is running\n".format(pid))
        sys.exit(0)

    def perform_action(self):
        """
        Process the command line parameters and perform the start, stop, restart, or status operations.
        """
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                self.start()
            elif 'stop' == sys.argv[1]:
                self.stop()
            elif 'restart' == sys.argv[1]:
                self.restart()
            elif 'status' == sys.argv[1]:
                self.status()
            else:
                print ("Unknown command")
                sys.exit(2)
            sys.exit(0)
        else:
            print ("Usage: {} start | stop | restart | status".format(sys.argv[0]))
            sys.exit(2)

    @abstractmethod
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """
        pass
