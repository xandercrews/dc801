# encoding: utf-8
import socket

REMOTE_ADDRESS = 'diehard.shallweplayaga.me'
REMOTE_PORT = 4001

import sys
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

import IPython

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((REMOTE_ADDRESS, REMOTE_PORT))
sf = s.makefile()

import re
EMPTY_PATTERN  = re.compile('^\s*$')

import collections

buffer = []

def myreadline(sobj):
    global buffer
    if len(buffer) > 0:
        line = ''.join(buffer).split('\n')[0]

        if line is None:
            log.error(line)
            _exit()

        buffer = buffer[len(line):]
        if len(buffer) > 0 and buffer[0] == '\n':
            buffer.pop(0)

        return line
    else:
        while True:
            buffer.append(sobj.read(1))

            if len(buffer) > 0 and buffer[-1] == '>':
                # log.debug(buffer)
                break
        return myreadline(sobj)

def _exit():
    s.close()
    sys.exit(1)

class JugSolver(object):
    SHELL_CALL_TABLE = {
        ('h', 'help'): '_help',
        ('i', 'ipython'): '_ipython',
        ('q', 'quit'): '_quit',
    }

    def __init__(self):
        self.messages = []
        self.action_queue = []

    def think(self):
        if len(self.action_queue) > 0:
            logging.debug('the time for thinking is over!')
            return
        if "Exits:" in self.messages[-1]:
            self.action_queue.extend(list('nnnnnnenwn'))
        else:
            # maybe search backwards for things we need to know?
            for message in self.messages.reverse():

    def do(self):
        thing_to_do = self.action_queue.pop(0)
        log.info('DOING: %s' % thing_to_do)
        log.debug('remaining queue: %s' % str(self.action_queue))
        self._send(thing_to_do)

    def _send(self, msg):
        msg = msg.strip() + "\n"
        log.debug('sending: %s' % msg.strip())
        s.send(msg)

    def _recv(self):
        while True:
            line = myreadline(sf)
            if line.endswith('>'):
                break
            self.messages.append(line)
            log.info('received: %s' % line)

    def _old_recv(self):
        while True:
            m = None
            m = sf.read(1)

            while True:
                if ord(m) == 27:
                    def readAndPrint(size=1):
                        m = sf.read(size)
                        logging.debug(m)
                        return m
                    while readAndPrint() != ';':
                        pass
                    readAndPrint(2)
                    m = sf.read(1)
                else:
                    break

            log.debug('first char: %s (%d)' % (m, ord(m),))
            if m not in ('>',):
                line = m + sf.readline(4096)
                line = line.strip()
                if EMPTY_PATTERN.match(line) is not None:
                    continue
                log.info(line)
                self.messages.append(line)
            else:
                break

    def _help(self):
        import pprint
        pprint.pprint(JugSolver.SHELL_CALL_TABLE)

    def _ipython(self):
        s = self._send
        l = self.messages[-1]

        IPython.embed()

    def _hooman(self):
        while True:
            call_table = JugSolver.SHELL_CALL_TABLE

            cmd = sys.stdin.readline()
            cmd = cmd.strip()

            if cmd in ('/q', '/quit'):
                return

            if cmd.startswith('/'):
                cmd = cmd.lstrip('/')

                cmd_method = None

                for c in call_table.keys():
                    if isinstance(c, collections.Sequence):
                        if cmd in c:
                            cmd_method = call_table[c]
                            break
                    else:
                        if cmd == c:
                            cmd_method = call_table[c]
                            break

                if cmd_method is None:
                    cmd_method = '_help'

                assert(hasattr(self, cmd_method))
                f = getattr(self, cmd_method)

                f()
            else:
                self._send(cmd)
                break

    def mainLoop(self):
        # log.info('receiving')
        self._recv()
        while True:
            # log.info('thinking')
            self.think()
            if len(self.action_queue) > 0:
                self.do()
            else:
                print 'dropping to interactive shell'
                self._hooman()
            self._recv()

if __name__ == '__main__':
    j = JugSolver()
    j.mainLoop()
    s.close()
