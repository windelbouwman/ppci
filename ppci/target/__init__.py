#!/usr/bin/env python

from .basetarget import Nop, Instruction, Label, Target, Comment, Alignment


class SimpleTarget(Target):
    def __init__(self):
        super().__init__('SimpleTarget')
