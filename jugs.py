# encoding: utf-8
import gevent.monkey
gevent.monkey.patch_all()

import StringIO
import functools
import pprint
import socket
import itertools
import time

rm = list('em.agayalpewllahs.draheid')
rm.reverse()
REMOTE_ADDRESS = ''.join(rm)
REMOTE_PORT = 4011 - 10

print (REMOTE_ADDRESS, REMOTE_PORT,)

import sys
import logging
import logging.config

import yaml

logyaml = """
version: 1
formatters:
    simple:
        format: '%(asctime)s - %(relativeCreated)d - %(name)s - %(levelname)s - %(message)s'
handlers:
    console:
        class: logging.StreamHandler
        level: DEBUG
        formatter: simple
        stream: ext://sys.stdout
root:
    level: DEBUG
    handlers: [console]
"""

sfh = StringIO.StringIO(logyaml)

logging.config.dictConfig(yaml.load(sfh))

log = logging.getLogger(__name__)

import IPython

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

import re
EMPTY_PATTERN  = re.compile('^\s*$')

import collections
import operator
import fractions

import gevent
import gevent.queue

buffer = []


class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args):
        if not isinstance(args, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)


# def myreadline(sobj):
#     buffer = []
#     while True:
#         buffer.append(sobj.read(1))
#
#         if len(buffer) > 0 and buffer[-1] == '>' or buffer[-1] == '\n':
#             log.debug(buffer)
#             break
#     return ''.join(buffer).strip()

def myreadline(sobj):

    global buffer
    while True:
        if len(buffer) > 0:
            # log.debug('buffer test')
            # log.debug(''.join(buffer).split('\n'))

            line = ''.join(buffer).split('\n')[0]

            if line is None:
                log.error(line)
                _exit()

            buffer = buffer[len(line):]

            if len(buffer) > 0 and buffer[0] == '\n':
                buffer.pop(0)

            # log.debug('line: %s' % line)
            # log.debug('remaining buffer: %s' % ''.join(buffer))

            return line
        else:
            try:
                while True:
                    res = sobj.recv(4096)
                    # log.debug('response: ' + res)
                    buffer.extend(res)

                    # log.debug(buffer)

                    if len(buffer) > 0 and "\n" in buffer:
                        # log.debug(buffer)
                        break
                    elif len(buffer) > 0 and ">" in buffer:
                        break
            except socket.error:
                gevent.sleep(0)

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
        self.action_queue = []

        self.message_queue = gevent.queue.Queue()
        self.ready_queue = gevent.queue.Queue()

        self.red = None
        self.blue = None
        self.target = None

    def _think(self):
        while True:
            self.think()
            gevent.sleep(0)

    def think(self):
        message = self.message_queue.get()

        log.info('thinking')

        if "Welcome John McClain" in message:
            self.action_queue.extend(list('nnnnnnenwn'))
        else:
            # maybe search backwards for things we need to know?

            if 'the center of the room is' in message:
                self.action_queue.extend(('get blue jug','get red jug',))
                self.action_queue.extend(('look red jug','look blue jug','look inscription',))
            elif 'red jug holds' in message:
                vol = re.search("of (\d+) gallons", message)
                self.red = int(vol.group(1))
            elif 'blue jug holds' in message:
                vol = re.search("of (\d+) gallons", message)
                self.blue = int(vol.group(1))
            elif 'To get to the next' in message:
                vol = re.search("(\d+) gallons", message)
                self.target = int(vol.group(1))

        if self.red is not None and self.blue is not None and self.target is not None:
                log.info('go time')
                soln = self.actionify_solution(self.red, self.blue, self.target)
                self.action_queue.extend(soln)
                if 'blue jug onto' in self.action_queue[-1]:
                    self.action_queue.append('drop red jug')
                else:
                    self.action_queue.append('drop blue jug')

                self.action_queue.append('n')

                self.ready_queue.put('')

                self.red = None
                self.blue = None
                self.target = None

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
    def weird_iterator(absbound=100):
        assert(absbound > 0)

        yield 0
        for ix in xrange(1, absbound):
            yield ix
            yield -ix


    # find m and n, for relative primes
    @staticmethod
    @memoized
    def m_n(red, blue, target):
        solns = []
        for m,n in itertools.permutations(list(JugSolver.weird_iterator(100)), 2):
            # log.debug('%d*%d + %d*%d == %s', red, m, blue, n, str(red*m+blue*n))
            if red*m + blue*n == target:
                solns.append((abs(m)+abs(n),m,n))

        if len(solns) == 0:
            raise Exception('found no solution')

        sorted(solns,key=operator.itemgetter(0),reverse=False)
        return solns[0][1], solns[0][2]



    @staticmethod
    def solve_jugs(red, blue, target):
        log.info('solving for %sg %sg -> %sg' % (red, blue, target,))

        m, n = JugSolver.m_n(red, blue, target)
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
        self._send(thing_to_do)
        log.debug('remaining queue: %s' % str(self.action_queue))

    def _send(self, msg):
        msg = msg.strip() + "\n"
        log.debug('sending: %s' % msg.strip())
        s.send(msg)

    def _recv(self):
        s.setblocking(0)

        while True:
            line = myreadline(s).strip()
            log.info('received: %s' % line)
            if line.endswith('>'):
                self.ready_queue.put(line)
            else:
                self.message_queue.put(line)

    def spawn_read_thread(self):
        self.rt = gevent.spawn(self._recv)

    def spawn_think_thread(self):
        self.tt = gevent.spawn(self._think)

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
        self.spawn_read_thread()
        self.spawn_think_thread()

        while True:
            self.ready_queue.get()

            while len(self.action_queue) == 0:
                gevent.sleep(0)
            self.do()

            # else:
            #     print 'dropping to interactive shell'
            #     self._hooman()


@memoized
def memo_gcd(a,b):
    return fractions.gcd(a,b)


class benchmark(object):
    def __init__(self,name,f):
        self.name = name
        self.f = f
    def __enter__(self):
        self.start = time.time()
    def __exit__(self,ty,val,tb):
        end = time.time()
        self.f("%s : %0.3f seconds" % (self.name, end-self.start))
        return False

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

    # precalculate all the relative primes under 100, and memoize all their
    # best solutions (sans the arrays to carry them out)
    # with benchmark('memoized all solutions in', log.info):
    #     relprimes = []
    #     with benchmark('calculated all relative primes < 100', log.info):
    #         for a,b in itertools.combinations(range(100),2):
    #             if memo_gcd(a,b) == 1:
    #                 relprimes.append((a,b,))
    #
    #     soln_count = 0
    #     with benchmark('memoized all solutions for relative prime pairs <100 (%s), and target=RED+BLUE' % len(relprimes), log.info):
    #         for a,b in relprimes:
    #             sum = max(a,b)
    #             for ix in xrange(1,sum):
    #                 try:
    #                     sn = JugSolver.m_n(a,b,sum)
    #                     soln_count += 1
    #                 except Exception,e:
    #                     pass
    #
    #     log.info('solution count: %d' % soln_count)

    log.info('connecting')
    s.connect((REMOTE_ADDRESS, REMOTE_PORT))

    j = JugSolver()
    j.mainLoop()
    s.close()
