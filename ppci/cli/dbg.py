""" Debugger command line utility. """


import argparse
import importlib
from .base import base_parser, march_parser, get_arch_from_args, LogSetup
from ..binutils.dbg import Debugger
from ..binutils.dbg.cli import DebugCli


parser = argparse.ArgumentParser(
    description=__doc__, parents=(march_parser, base_parser))
parser.add_argument(
    '--driver',
    help='debug driver to use. Specify in the format: module:class',
    default='ppci.binutils.dbg:DummyDebugDriver')


def dbg(args=None):
    """ Run dbg from command line """
    args = parser.parse_args(args)
    with LogSetup(args):
        march = get_arch_from_args(args)
        driver_module_name, driver_class_name = args.driver.split(':')
        driver_module = importlib.import_module(driver_module_name)
        driver_class = getattr(driver_module, driver_class_name)
        driver = driver_class()
        debugger = Debugger(march, driver)
        cli = DebugCli(debugger)
        cli.cmdloop()


if __name__ == '__main__':
    dbg()
