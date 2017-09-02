from .transform import FunctionPass


class TailCallOptimization(FunctionPass):
    """ Tail call optimization.

    This optimization replaces calls to the function
    itself with jumps.

    For example, the following function contains a tail call:

    i32 fib(i32 n)
    {
      block0: {
        cjmp n > 0 ? block1 : block2
      }

      block1: {
        return call fib(n - 2)
      }

      block2: {
        i32 c = 1;
        return c;
      }
    }

    It could also become this:

    i32 fib(i32 n)
    {
      block3: {  // entry
        jmp block0;
      }

      block0: {
        i32 n_phi = {block3: n, block1: n2}
        cjmp n_phi > 0 ? block1 : block2
      }

      block1: {
        i32 n2 = n_phi - 2;
        jmp block0;
      }

      block2: {
        i32 c = 1;
        return c;
      }
    }

    In the latter case, the return call combination is replaced
    with a jump to the start of the function.
    """
    def on_function(self, function):
        # Check if there are any tail calls. If not, we are done.
        tail_calls = []
        for block in function:
            if len(block) >= 2 and \
                    isinstance(block[-1], ir.Return) and \
                    isinstance(block[-2], ir.FunctionCall) and \
                    block[-2] is block[-1].value:
                tail_calls.append(block[-1])

        # No tail calls in this function, we are done.
        if not tail_calls:
            return

        z = []
        z.append((function.entry, function.arguments))

        # Insert phi nodes for each argument:
        arg_phis = []
        for argument in function.arguments:
            arg_phi = ir.Phi(argument.name, argument.ty)
            argument.replace_usage_by(arg_phi)
            arg_phis.append(arg_phi)

            # Add the trivial input branch for the phi node from entry:
            arg_phi.add_input(entry, arg_value)

        assert all(isinstance(tc, ir.Call) for tc in tail_calls)

        # Replace tail calls by call to new block
        for tail in tail_calls:
            tail_call = tail.value
            block = tail.block

            # Replace tail call by jump:
            tail.remove()
            tail_call.remove()
            block.append(ir.Jump(entry2))

            # Add input for all arguments to the argument phis:
            for arg_phi, arg_value in zip(arg_phis, tail_call.arguments):
                arg_phi.add_input(block, arg_value)
