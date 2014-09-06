
import cProfile
import unittest
import pstats
import testsamples
import logging
import logging.handlers
import shutil
import os
import testsamples

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logformat = '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
    ch.setFormatter(logging.Formatter(logformat))
    logging.getLogger().addHandler(ch)
    uh = logging.handlers.DatagramHandler('localhost', 9021)
    uh.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(uh)
    logger = logging.getLogger('run')
    logger.info('Starting profiling')
    loader = unittest.TestLoader()
    # suite = loader.loadTestsFromName('TestSamplesOnVexpress.testBrainFuckQuine', module=testsamples)
    suite = loader.loadTestsFromName('TestSamplesOnVexpress.testBrainFuckHelloWorld', module=testsamples)
    tc = testsamples.TestSamplesOnVexpress()
    # tc.testBrainFuckHelloWorld()
    # tc.testBrainFuckQuine()

    def runtests():
        unittest.TextTestRunner().run(suite)

    # s = cProfile.run('runtests()',sort='cumtime')
    p = cProfile.Profile()
    s = p.run('runtests()')
    stats = pstats.Stats(p)
    stats.dump_stats('results.cprofile')
    # stats.sort_stats('tottime')
    stats.sort_stats('cumtime')
    # stats.print_stats(.1)

    # Convert result profile to kcachegrind format:
    if shutil.which('pyprof2calltree'):
        os.system('pyprof2calltree -i results.cprofile')
