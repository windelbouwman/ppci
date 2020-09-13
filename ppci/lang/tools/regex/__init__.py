""" Regular expression routines.

Implement regular expressions using derivatives.

Largely copied from: https://github.com/MichaelPaddon/epsilon

Implementation of this logic:
https://en.wikipedia.org/wiki/Brzozowski_derivative

"""

import bisect
from .regex import Symbol, SymbolSet, Kleene, EPSILON, NULL
from .parser import parse
from .compiler import compile


def scan(prog, chars):
    """Bad-ass statemachine."""
    state_transitions, accept_states, error_state = prog
    offset = 0
    start = 0
    state = 0
    accept = False
    while True:
        print("state machine, state={}, offset={}".format(state, offset))
        if accept_states[state]:
            accept = accept_states[state]
            end = offset

        if offset < len(chars):
            char = ord(chars[offset])
            transition = pick_transition(state_transitions[state], char)
            state = transition[2]
            offset += 1
        else:
            state = error_state

        if state == error_state:
            if accept:
                txt = chars[start:end]
                yield txt
                # Start over:
                start = end
                state = 0
                accept = False
                end = 0

            elif offset > start:
                raise ValueError("No match!")
            else:
                break
    print("DONE&DONE")


def pick_transition(transitions, char):
    i = bisect.bisect(transitions, (char,))
    if i < len(transitions) and char == transitions[i][0]:
        transition = transitions[i]
    elif i > 0 and transitions[i - 1][0] <= char <= transitions[i - 1][1]:
        transition = transitions[i - 1]
    else:
        raise RuntimeError("We should not get here!")
    return transition


__all__ = ("parse", "compile", "Symbol", "SymbolSet", "Kleene")
