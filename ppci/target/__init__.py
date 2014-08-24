#!/usr/bin/env python

from .basetarget import Nop, Instruction, Label, Target, Comment, Alignment


class SimpleTarget(Target):
    def __init__(self):
        super().__init__('SimpleTarget')


def get_target(name):
    """ Delay the loading of the target until requested """
    from . import target_list
    return target_list.targets[name]
