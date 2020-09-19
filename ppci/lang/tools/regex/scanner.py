import functools
import bisect
from .regex import ExpressionVector
from .compiler import compile
from .parser import parse


def scan(prog, chars):
    """Bad-ass statemachine."""
    state_transitions, accept_states, error_state = prog
    start = offset = 0
    state = 0
    accept = False
    while True:
        # print("state machine, state={}, offset={}".format(state, offset))
        if accept_states[state]:
            accept = accept_states[state]
            end = offset

        if offset < len(chars):
            char = ord(chars[offset])
            state = pick_transition(state_transitions, state, char)
            offset += 1
        else:
            state = error_state

        if state == error_state:
            if accept:
                txt = chars[start:end]
                yield txt
                # Start over:
                offset = start = end
                state = 0
                accept = False

            elif offset > start:
                raise ValueError("No match!")
            else:
                break
    # print("DONE&DONE")


def pick_transition(state_transitions, state, char):
    """Determine next state."""
    transitions = state_transitions[state]

    i = bisect.bisect(transitions, (char,))
    if i < len(transitions) and char == transitions[i][0]:
        transition = transitions[i]
    elif i > 0 and transitions[i - 1][0] <= char <= transitions[i - 1][1]:
        transition = transitions[i - 1]
    else:
        raise RuntimeError("We should not get here!")
    return transition[2]


def make_scanner(token_descriptions):
    """Create a scanner based upon a set of token descriptions."""
    vector = []
    for name in token_descriptions:
        r = token_descriptions[name]
        expr = parse(r)
        print(name, expr)
        vector.append((name, expr))

    vector = ExpressionVector(vector)

    prog = compile(vector)

    return Scanner(prog)


class Scanner:
    def __init__(self, prog):
        self._state = 0
        self._prog = prog

    def scan(self, txt):

        # Initialize some variables:
        (
            self._state_transitions,
            self._accept_states,
            self._error_state,
        ) = self._prog
        self._start = self._offset = 0
        self._state = 0
        self._accept = False

        while True:
            # Check if we are in accepting state:
            if self._accept_states[self._state]:
                self._accept = self._accept_states[self._state]
                # print("Accept", self._accept)
                end = self._offset

            if self._offset < len(txt):
                char = ord(txt[self._offset])
                self._state = pick_transition(
                    self._state_transitions, self._state, char
                )
                self._offset += 1
            else:
                self._state = self._error_state

            if self._state == self._error_state:
                if self._accept:
                    token_txt = txt[self._start : end]
                    # print(self._state, token_txt)

                    yield (self._accept[0], token_txt)
                    # Start over:
                    self._offset = self._start = end
                    self._state = 0
                    self._accept = False

                elif self._offset > self._start:
                    raise ValueError("No match!")
                else:
                    break
