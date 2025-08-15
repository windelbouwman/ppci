"""Generate code for a scanner.

This can be used to create a C file which does the scanning
of tokens.
"""

C_PROLOGUE = """

struct state_transition {
    int start;
    int end;
    int next_state;
};

typedef struct state_transition state_transition_t;

"""


def generate_code(prog, f):
    """Generate some C code."""
    state_transitions, accept_states, error_state = prog
    # with open(filename, 'w') as f:
    print(C_PROLOGUE, file=f)

    # Create tables for transitions:
    for nr, transition in enumerate(state_transitions):
        print(f"state_transition_t transitions_state_{nr}[] = ", file=f)
        for start_char, end_char, next_state in transition:
            print(
                f"    {{ {start_char}, {end_char}, {next_state} }},",
                file=f,
            )
        print("};", file=f)
        print(file=f)

    # Create table with transition pointers:
    print(
        f"state_transition_t* transitions[{len(state_transitions)}] = {{",
        file=f,
    )
    for nr, _ in enumerate(state_transitions):
        print(f"    &transitions_state_{nr},", file=f)
    print("};", file=f)
    print(file=f)

    # Create value with error state:
    print(f"int error_state = {error_state};", file=f)
    print(file=f)

    # Create accepting states:
    print(f"int accept_states[{len(accept_states)}] = {{", file=f)
    for accept in accept_states:
        if accept:
            print("    1,", file=f)
        else:
            print("    0,", file=f)
    print("};", file=f)
    print(file=f)
