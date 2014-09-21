from ppci.irmach import AbstractInstruction


class InstructionSelector:
    """
        Base instruction selector. This class must be inherited by
        backends.
    """
    def newTmp(self):
        return self.frame.new_virtual_register()

    def munch_dag(self, dags, frame):
        """ Consume a dag and match it using the matcher to the frame """
        # Entry point for instruction selection

        # Enter a frame per function:
        self.frame = frame

        # Template match all trees:
        for dag in dags:
            for root in dag:
                if type(root) is AbstractInstruction:
                    self.emit(root)
                else:
                    # Invoke dynamic programming matcher machinery:
                    self.matcher.gen(root)
            frame.between_blocks()

    def munchCall(self, e):
        """ Generate code for call sequence """
        label, args, res_var = e
        self.frame.gen_call(label, args, res_var)

    def move(self, dst, src):
        """ Generate move """
        self.frame.move(dst, src)

    def emit(self, *args, **kwargs):
        """ Abstract instruction emitter proxy """
        return self.frame.emit(*args, **kwargs)
