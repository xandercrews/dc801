# encoding: utf-8
import pprint
import socket
import itertools

rm = list('em.agayalpewllahs.draheid')
rm.reverse()
REMOTE_ADDRESS = ''.join(rm)
REMOTE_PORT = 4011 - 10

print (REMOTE_ADDRESS, REMOTE_PORT,)

import sys
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

import IPython

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((REMOTE_ADDRESS, REMOTE_PORT))
sf = s.makefile()

import re
EMPTY_PATTERN  = re.compile('^\s*$')

import collections
import operator

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
            r_messages = self.messages[:]
            r_messages.reverse()

            for message in r_messages:
                if 'red jug is sitting' in message:
                    self.action_queue.extend(('look inscription','look red jug','look blue jug'))
                    break
                elif 'red jug holds' in message:
                    vol = re.search("of (\d+) gallons", message)
                    red = int(vol.group(1))
                elif 'blue jug holds' in message:
                    vol = re.search("of (\d+) gallons", message)
                    blue = int(vol.group(1))
                elif 'To get to the next stage put' in message:
                    vol = re.search("(\d+) gallons", message)
                    target = int(vol.group(1))
                    soln = self.actionify_solution(red, blue, target)
                    self.action_queue.extend(('get blue jug','get red jug',))
                    self.action_queue.extend(soln)
                    self.action_queue.extend(('drop red jug','drop blue jug','n'))
                    break

    def old_actionify_solution(self, red, blue, target):
        if target == 4:
            return ['fill blue jug','pour blue jug into red jug','empty red jug','pour blue jug into red jug','fill blue jug',
                    'pour blue jug into red jug', 'put blue jug onto scale']
        else:
            return self.solve_jugs(red, blue, target)

    def actionify_solution(self, red, blue, target):
        return self.solve_jugs(red, blue, target)

    @staticmethod
    def solution_1(red, blue, target, m, n):
        assert(n < 0)       # we're emptying blue
        assert(red < blue)  # blue is bigger
        redset = ['fill red jug' for ix in range(abs(m))]
        blueset = ['empty blue jug' for ix in range(abs(n))]

        mergeset = []

        bluevol = 0

        while len(redset) > 0 or len(blueset) > 0:
            while red + bluevol < blue:
                mergeset.append(redset.pop())
                mergeset.append('pour red jug into blue jug')
                bluevol += red

                if bluevol == target:
                    break

            if len(blueset) > 0:
                mergeset.append(redset.pop())
                mergeset.append('pour red jug into blue jug')
                mergeset.append(blueset.pop())

                redvol = (red + bluevol) - blue
                bluevol = 0

                if redvol == target:
                    break

                else:
                    mergeset.append('pour red jug into blue jug')
                    bluevol = redvol

        if bluevol == target:
            mergeset.append('put blue jug onto scale')
        elif redvol == target:
            mergeset.append('put red jug onto scale')
        else:
            log.error(mergeset)
            log.error('%d %d %d %d %d', red, blue, target, m, n)
            raise Exception('wut happened?')

        return mergeset

    @staticmethod
    def solution_2(red, blue, target, m, n):
        assert(n < 0)   # we're emptying blue
        assert(red > blue)  # red is bigger

        redset = ['fill red jug' for ix in range(abs(m))]
        blueset = ['empty blue jug' for ix in range(abs(n))]

        mergeset = []

        redvol = 0
        bluevol = 0

        while len(redset) > 0 or len(blueset) > 0:
            mergeset.append(redset.pop())
            redvol = red

            while redvol - blue > 0:
                mergeset.append('pour red jug into blue jug')
                mergeset.append(blueset.pop())
                redvol -= (blue - bluevol)
                bluevol = 0

                if redvol == target:
                    mergeset.append('put red jug onto scale')
                    break

            if redvol == target:
                break

            mergeset.append('pour red jug into blue jug')

            bluevol = redvol
            redvol = 0

        if bluevol == target:
            mergeset.append('put blue jug onto scale')
        elif redvol != target:
            log.error(mergeset)
            log.error(red, blue, target, m, n)
            raise Exception('wut happened?')

        return mergeset

    @staticmethod
    def solution_3(red, blue, target, m, n):
        assert(m < 0)
        assert(red < blue)

        redset = ['empty red jug' for ix in range(abs(m))]
        blueset = ['fill blue jug' for ix in range(abs(n))]

        mergeset = []

        bluevol = 0
        redvol = 0

        while len(blueset) > 0 or len(redset) > 0:
            mergeset.append(blueset.pop())
            bluevol = blue

            while bluevol - red > 0:
                mergeset.append('pour blue jug into red jug')
                mergeset.append(redset.pop())
                bluevol -= (red - redvol)
                redvol = 0

                if bluevol == target:
                    mergeset.append('put blue jug onto scale')
                    break

            if bluevol == target:
                break

            mergeset.append('pour blue jug into red jug')

            redvol = bluevol
            bluevol = 0

        if redvol == target:
            mergeset.append('put red jug onto scale')
        elif bluevol != target:
            log.error(mergeset)
            log.error(blue, red, target, m, n)
            raise Exception('wut happened?')

        return mergeset


    @staticmethod
    def solution_4(red, blue, target, m, n):
        assert(m < 0)
        assert(red > blue)

        redset = ['empty red jug' for ix in range(abs(m))]
        blueset = ['fill blue jug' for ix in range(abs(n))]

        mergeset = []

        redvol = 0

        while len(blueset) > 0 or len(redset) > 0:
            while blue + redvol < red:
                mergeset.append(blueset.pop())
                mergeset.append('pour blue jug into red jug')
                redvol += blue

                if redvol == target:
                    break

            if len(redset) > 0:
                mergeset.append(blueset.pop())
                mergeset.append('pour blue jug into red jug')
                mergeset.append(redset.pop())

                bluevol = (blue + redvol) - red
                redvol = 0

                if bluevol == target:
                    break

                else:
                    mergeset.append('pour blue jug into red jug')
                    redvol = bluevol

        if redvol == target:
            mergeset.append('put red jug onto scale')
        elif bluevol == target:
            mergeset.append('put blue jug onto scale')
        else:
            log.error(mergeset)
            log.error('%d %d %d %d %d', red, blue, target, m, n)
            raise Exception('wut happened?')

        return mergeset

    @staticmethod
    def solution_5(red, blue, target, m, n):
        assert(m == 0 or n == 0)        # one's zero
        assert(m > 0 or n > 0)      # the other is positive

        solution = []

        if m > 0:
            color = 'red'
            holder = 'blue'
            unit = red
            assert(blue > target)     # blue needs to be big enough to hold target
            assert(red < target)      # red needs to be smaller and ...
            assert(target % red == 0) # .. a factor
        else:
            color = 'blue'
            holder = 'red'
            unit = blue
            assert(red > target)       # red needs to be big enough to hold target
            assert(blue < target)      # blue needs to be smaller and ...
            assert(target % blue == 0) # .. a factor

        vol = 0

        while vol < target:
            solution.extend(('fill %s jug' % color,'pour %s jug into %s jug' % (color, holder,),))
            vol += unit

        if vol != target:
            raise Exception('ah shit. really? fuck you sleep, you win')

        solution.append('put %s jug onto scale' % holder)

        return solution


    @staticmethod
    def solve_jugs(red, blue, target):
        log.info('solving for %sg %sg -> %sg' % (red, blue, target,))

        def weird_iterator(absbound=100):
            assert(absbound > 0)

            yield 0
            for ix in xrange(1, absbound):
                yield ix
                yield -ix

        # find m and n
        def m_n():
            solns = []
            for m,n in itertools.permutations(list(weird_iterator(40)), 2):
                # log.debug('%d*%d + %d*%d == %s', red, m, blue, n, str(red*m+blue*n))
                if red*m + blue*n == target:
                    solns.append((abs(m)+abs(n),m,n))

            if len(solns) == 0:
                raise Exception('found no solution')

            sorted(solns,key=operator.itemgetter(0),reverse=False)
            log.info('pours: %d' % solns[0][0])
            return solns[0][1], solns[0][2]

        m, n = m_n()
        log.info('red %d blue %d' % (m,n,))

        # try each solution, which is responsible for asserting its own assumptions
        for soln in (JugSolver.solution_1, JugSolver.solution_2, JugSolver.solution_3, JugSolver.solution_4,
                     JugSolver.solution_5,):
        # for soln in (JugSolver.solution_3,):
            try:
                return soln(red, blue, target, m, n)
            except AssertionError, e:
                pass

        raise Exception('i haz the dumb nao!')

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
    # s = JugSolver.solve_jugs(19,67,65) # soln_1 ?
    # s = JugSolver.solve_jugs(5,37,28) # soln_1 ?
    # s = JugSolver.solve_jugs(53,23,19) # soln_2
    # s = JugSolver.solve_jugs(83,41,48) # soln_2 ?
    # s = JugSolver.solve_jugs(3,5,4) # soln_3?
    # s = JugSolver.solve_jugs(31,29,5) # soln_4?
    # s = JugSolver.solve_jugs(61, 3, 6) # soln_5 ?
    # pprint.pprint(s, indent=2)
    # sys.exit(1)

    j = JugSolver()
    j.mainLoop()
    s.close()
