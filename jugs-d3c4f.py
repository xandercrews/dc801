import getpass
import socket
import sys
import telnetlib
import re
 
def goDirection(tn, direction):
    tn.write(direction)
    tn.write("\n")

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
 
#initial maze n n n n n n e n w n
def solveMaze1(tn):
    maze1 = ["n", "n", "n", "n", "n", "n", "e", "n", "w", "n"]
    for dir in maze1:
        tn.write(dir)
        tn.write("\n")
        tn.read_until(">",60)
   
@memoized
def solveJugs(jugACapacity, jugAName, jugBCapacity, jugBName, desiredGals):
    maxPourCount = 150
    pourArray = []
    jugACurrent = 0
    jugBCurrent = 0
    pourCount = 0
    foundPourCount = False
 
    if jugACapacity == desiredGals:
        pourArray.append("drop "+jugBName+" jug")
        pourArray.append("put "+jugAName+" jug onto scale")
        return pourArray
 
    if jugBCapacity == desiredGals:
        pourArray.append("drop "+jugAName+" jug")
        pourArray.append("put "+jugBName+" jug onto scale")
        return pourArray
       
    while foundPourCount == False and pourCount < maxPourCount:
        pourCount += 1
        pourArray.append("fill "+jugAName+" jug")
        jugACurrent = jugACapacity
           
        while jugACurrent > 0:
            pourCount += 1
            pourArray.append("pour "+jugAName+" jug into "+jugBName+" jug")
            jugBCurrent += jugACurrent
            jugACurrent = 0
            if jugBCurrent > jugBCapacity:
                jugACurrent = jugBCurrent - jugBCapacity
                jugBCurrent = jugBCapacity
 
            if jugACurrent == desiredGals:
                pourArray.append("drop "+jugBName+" jug")
                pourArray.append("put "+jugAName+" jug onto scale")
                foundPourCount = True
                break
               
            if jugBCurrent == jugBCapacity:
                pourArray.append("empty "+jugBName+" jug")
                jugBCurrent = 0
 
            if jugBCurrent == desiredGals:
                pourArray.append("drop "+jugAName+" jug")
                pourArray.append("put "+jugBName+" jug onto scale")
                foundPourCount = True
                break
               
    if foundPourCount == False:
        pourArray = []
    return pourArray

@memoized
def solveJugsBest(blueJug, redJug, gals):
    foundIt = solveJugs(blueJug,"blue",redJug,"red",gals)
    foundIt2 = solveJugs(redJug,"red",blueJug,"blue",gals)
 
    if len(foundIt) <= len(foundIt2) and len(foundIt) > 0:
        return foundIt
    elif len(foundIt2) < 1 and len(foundIt) > 0:
        return foundIt
    elif len(foundIt2) > 0:
        return foundIt2
    else:
        return []

JUG_PATTERN = re.compile(' [0-9]* ')
 
def parseJugText(textToParse):
    m = JUG_PATTERN.search(textToParse)
    return int(m.group(0))

CAP_PATTERN = re.compile('get to the next stage put ([0-9]*) gallons')
RED_PATTERN = re.compile('A red jug holds 0 of ([0-9]*) gallons')
BLUE_PATTERN = re.compile('A blue jug holds 0 of ([0-9]*) gallons')

def solveRoom(tn):
    infoCommands = ["look inscription","look blue jug","look red jug","get red jug","get blue jug"]
    for infoCommand in infoCommands:
        tn.write(infoCommand+"\n")
 
    textToParse = tn.read_until("red jug holds",60)
    textToParse += tn.read_until("gallons",60)

    m = CAP_PATTERN.search(textToParse)
    capacity = int(m.group(1))
 
    m = BLUE_PATTERN.search(textToParse)
    blueJug = int(m.group(1))

    m = RED_PATTERN.search(textToParse)
    redJug = int(m.group(1))

    commands = solveJugsBest(blueJug, redJug, capacity)

    for command in commands:
        tn.write(command+"\n")
 
    tn.write("n\n")


def getKey(tn):
    infoCommands = ['get key', 'look key', 'n', 's' ,'e', 'w']
    for infoCommand in infoCommands:
        tn.write(infoCommand+"\n")
    while True:
        msg = tn.get_socket().recv(4096)
        if len(msg) > 0:
            print msg,

import fractions
import itertools
import time
import collections
import fractions

@memoized
def memo_gcd(a,b):
    return fractions.gcd(a,b)

class benchmark(object):
    def __init__(self,name):
        self.name = name
    def __enter__(self):
        self.start = time.time()
    def __exit__(self,ty,val,tb):
        end = time.time()
        print "%s : %0.3f seconds" % (self.name, end-self.start)
        return False

# attempt to pre-solve some
with benchmark('memoized all solutions in'):
    relprimes = []
    with benchmark('calculated all relative primes < 100'):
        for a,b in itertools.combinations(range(100),2):
            if memo_gcd(a,b) == 1:
                relprimes.append((a,b,))

    soln_count = 0
    with benchmark('memoized all solutions for relative prime pairs <100'):
        for a,b in relprimes:
            _sum = max(a,b)
            for ix in range(1,_sum):
                solveJugsBest(a, b, _sum)
                soln_count += 1

    print soln_count, 'solutions'


INROOM_PATTERN = re.compile('A ([a-zA-Z0-9 ]+) is sitting in the room')

#  MAIN CODE EXECUTION STARTS HERE
HOST = "diehard.shallweplayaga.me"
PORT = "4001"
tn = telnetlib.Telnet(HOST, PORT)
tn.get_socket().setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

#  initial connection. wait for prompt
print tn.read_until("mysterious field",60)
solveMaze1(tn)
tn.read_until(">",60)

roomsSolved=0
backlog =""


while True:
    try:
        with benchmark('solved room %d' % roomsSolved):
            solveRoom(tn)
        roomsSolved +=1

        toParse = tn.read_until("is sitting in the room", 60)
        m = INROOM_PATTERN.search(toParse)
        if m is None:
            print m
            continue
        whatshere = m.group(1)

        if whatshere not in ('red jug', 'fountain', 'blue jug', 'scale',):
            print whatshere
            getKey(tn)
        else:
            print whatshere

    except Exception, e:
        print "!===! Room:",roomsSolved, "solved !===!"
        raise
