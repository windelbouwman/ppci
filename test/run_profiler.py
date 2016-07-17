
from cProfile import Profile
import pstats
import logging
import logging.handlers
from os import path
import shutil
import os


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logformat = '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
    ch.setFormatter(logging.Formatter(logformat))
    logging.getLogger().addHandler(ch)
    logger = logging.getLogger('run')
    logger.info('Starting profiling')

    def run_somecommand():
        from ppci.api import construct
        print(construct)
        construct('../examples/linux64/fib/build.xml')

    p = Profile()
    s = p.run('run_somecommand()')
    stats = pstats.Stats(p)
    stats.dump_stats('results.cprofile')
    stats.sort_stats('cumtime')

    logger.info('Done profiling')

    # Convert result profile to kcachegrind format:
    if shutil.which('pyprof2calltree'):
        os.system('pyprof2calltree -i results.cprofile')
