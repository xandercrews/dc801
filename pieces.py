__author__ = 'achmed'

testBoard = """

-------------------
|     |     |     |
|  1  |  2  |  3  |
|     |     |     |

-------------------
|     |     |     |
|     |  5  |  8  |
|     |     |     |

-------------------
|     |     |     |
|  4  |  6  |  7  |
|     |     |     |
-------------------


"""

realBoard = """
                                              -------------------
|     |     |     |
|  8  |  3  |  2  |
|     |     |     |

-------------------
|     |     |     |
|  7  |  5  |  6  |
|     |     |     |

-------------------
|     |     |     |
|  1  |  4  |     |
|     |     |     |
-------------------

"""

import sys
from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(mode='Verbose',
                                     color_scheme='Linux', call_pdb=1)

import socket

import re
ONLYSPACES = re.compile('^\s+$')

def intsAndSpaces(s):
    try:
        if ONLYSPACES.match(s) is not None:
            return 0
        return int(s)
    except Exception:
        return None

def parseBoard(b):
    board = []
    for line in b.split("\n"):
        if '----' in line:
            continue
        elif '|' in line:
            col = line.split('|')
            nums = filter(lambda c: c is not None, map(intsAndSpaces, col))
            if sum(nums) == 0:
                continue
            board.extend([nums])
    return board

import board
import solver

if __name__ == '__main__':
    b = parseBoard(realBoard)
    solu = board.board(3)
    bobj = board.board(3, b)
    starsolver = solver.a_start_solver()
    steps = starsolver.a_star(bobj, solu)
    for step in steps:
        step.show_state()