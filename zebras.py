#------------- logging
import StringIO
import sys
import logging
import logging.config
import operator
import time

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
    level: INFO
    handlers: [console]
"""

sfh = StringIO.StringIO(logyaml)

logging.config.dictConfig(yaml.load(sfh))

log = logging.getLogger(__name__)
#-------------

import pprint
import socket
import telnetlib

class StopException(Exception):
    pass

def start_game(tn):
    welcome = tn.read_until('Press return to start')
    tn.write('\n')

    log.debug('welcome:\n %s\n <<<' % welcome)

def read_track(tn):
    garbage = tn.read_until('|-')
    garbage = garbage[:-2]
    if garbage != '' and not garbage.isspace():
        log.warn('garbage:\n %s\n <<<' % garbage)

    track = '|-'
    track += tn.read_until('-|\n')
    track += tn.read_until('-|\n')

    return track

def parse_track(track):
    track_arr = []
    for line in track.split('\n'):
        if line == '' or line.isspace():
            continue

        if line == '|-----|':
            continue

        if len(line) < 7 or line[0] != '|' or line [6] != '|':
            log.warn('thing while parsing track:\n %s\n <<<' % line)
            continue

        assert(line[0] == '|' and line[6] == '|')

        track_arr.append(list(line[1:6]))

    return track_arr

#--------------- zebra objects
class ZebraObject(object):
    def __init__(self, label, x, y):
        self.label = label
        self.x = x
        self.y = y

    # 'lead' is the number of lanes away from the object
    @property
    def lead(self, other):
        return self.y - other.y

    def __repr__(self):
        return '<%s (%d,%d)>' % (self.__class__.__name__, self.x, self.y,)

class Person(ZebraObject):
    pass

class You(ZebraObject):
    pass

class Car(ZebraObject):
    pass

class Snake(ZebraObject):
    pass

class BigZebra(ZebraObject):
    pass

class Tree(ZebraObject):
    pass

class RoadBlock(ZebraObject):
    pass

class Rock(ZebraObject):
    pass

class ZebraObjectFactory(object):
    OBJ_TABLE = {
        'u': You,
        'P': Person,
        'r': Rock,
        'c': Car,
        '~': Snake,
        'Z': BigZebra,
        'T': Tree,
        'X': RoadBlock,
    }

    @staticmethod
    def objectify(label, x, y):
        if label == ' ':
            return None
        elif label not in ZebraObjectFactory.OBJ_TABLE:
            raise Exception('unknown thing %s' % label)
        else:
            return ZebraObjectFactory.OBJ_TABLE[label](label, x, y)
#-------------------

def objectify_track(track):
    things = []
    row = 1

    you = None

    for span in track:
        col = 1
        for lane_item in span:
            o = ZebraObjectFactory.objectify(lane_item,col,row)
            if isinstance(o, You):
                assert(you is None)
                you = o
            elif o is not None:
                things.append(o)
            col += 1
        row += 1

    log.debug('things: %s', [ you ] + things)

    return you, things

def _chess_solver(x,y,d,path=[]):
    if y < 1:
        # you made it
        yield path
    else:
        # check for collisions
        if (x,y,) not in d:
            if x > 1:
                for soln in _chess_solver(x-1,y-1,d,path + ['l']):
                    yield soln
            for soln in _chess_solver(x,y-1,d,path + ['']):
                yield soln
            if x < 5:
                for soln in _chess_solver(x+1,y-1,d,path + ['r']):
                    yield soln
        else:
            log.debug('collide with %s on %s' % (d[(x,y,)], path))

def closest_obstacle_row(things):
    assert(len(things) > 0)
    closest = filter(lambda t: t.y != you.y, things)        # filter
    closest = sorted(closest, key=operator.attrgetter('y'), reverse=True)
    closest = filter(lambda thing: thing.y == closest[0].y, closest)
    return closest

def chess_the_path(you, things):
    thingdict = dict({(t.x,t.y): None for t in things})

    min_turns = 99
    chosen_solution = None

    def rel_x(c):
        if c == '':
            return 0
        elif c == 'l':
            return -1
        elif c == 'r':
            return 1
        else:
            raise Exception('wut?')

    best_position = 99

    for solution in _chess_solver(you.x,you.y,thingdict):
        # num_turns = sum(map(lambda c: 1 if c == '' else 0, solution))
        # if num_turns < min_turns:
        #     chosen_solution = solution

        new_position = you.x + sum(map(rel_x, solution))
        if abs(new_position - 3) < abs(best_position - 3):
            best_position = new_position
            chosen_solution = solution

    if chosen_solution is None:
        raise Exception('no solution, prepare your anus')
    else:
        log.info('solution: %s' % chosen_solution)
        log.info('solution end position %d' % best_position)

    return chosen_solution[0]

def decide_move(you, things):
    LEFT = 'l'
    RIGHT = 'r'
    HOLD = ''

    # if there's nothing on the radar, just get back to the middle
    if len(things) == 0:
        if you.x != 3:
            log.info('thought: nothing here, reset position')
            if you.x < 3:
                return RIGHT
            else:
                return LEFT
        else:
            log.info('thought: fucking coast')
            return HOLD

    # determine the closest obstacles, don't worry about things on the same row
    c = closest_obstacle_row(things)
    if len(c) > 0:
        # calculate the possible holes
        c_cols = map(operator.attrgetter('x'), c)
        holes = [x for x in range(1,6) if x not in c_cols]

        if len(holes) > 1:
            # decision point, which hole do we take?
            # simulate what would happen if we went that way?
            start_t = time.time()
            next_move = chess_the_path(you, things)
            log.info('chess path took: %f' % (time.time() - start_t))
            return next_move
        else:
            log.info('thought: only one choice')

            target_hole = holes[0] # lol, which hole is #0
            # target_hole = sorted(holes, key=lambda h: abs(3-h))[0] # lol

            if you.x > target_hole:
                return LEFT
            elif you.x < target_hole:
                return RIGHT
    else:
        log.info('fucking coast v2')

    return HOLD

def send_move(tn, move):
    if move == '':
        verb = 'NOWHERE'
    elif move == 'l':
        verb = 'LEFT'
    elif move == 'r':
        verb = 'RIGHT'

    log.info('moving %s', verb)

    tn.write(move+"\n")

##------------ go time
HOST = 'grandprix.shallweplayaga.me'
PORT = 2038

tn = telnetlib.Telnet(HOST, PORT)
tn.get_socket().setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

start_game(tn)


while True:
    try:
        # parse the track
        hooman_readable_track = read_track(tn)

        print hooman_readable_track

        t = parse_track(hooman_readable_track)

        # make object list from the
        you, things = objectify_track(t)

        # decide and move
        move = decide_move(you, things)
        send_move(tn, move)

    except EOFError, e:
        log.error('game over')
        break

    except StopException, e:
        print hooman_readable_track
        log.error('stop')
        break

tn.close()
