#------------- logging
import StringIO
import sys
import logging
import logging.config
import operator

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

def closest_obstacle_row(things):
    assert(len(things) > 0)
    closest = sorted(things, key=operator.attrgetter('y'), reverse=True)
    closest = filter(lambda thing: thing.y == closest[0].y, closest)
    return closest

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
    c = closest_obstacle_row(filter(lambda t: t.y != you.y, things))

    # calculate the possible holes
    c_cols = map(operator.attrgetter('x'), c)
    holes = [x for x in range(1,6) if x not in c_cols]

    if len(holes) > 1:
        # decision point, which hole do we take?
        # simulate what would happen if we went that way?
        log.info('thought: possible paths: %s' % holes)
        target_hole = holes[0] # lol
    else:
        log.info('thought: only one choice')
        target_hole = holes[0] # lol

    if you.x > target_hole:
        return LEFT
    elif you.x < target_hole:
        return RIGHT

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

tn.close()
