
import cProfile
import unittest
import pstats
import test_samples
import logging
import logging.handlers
import shutil
import os


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logformat = '%(asctime)s|%(levelname)s|%(name)s|%(message)s'
    ch.setFormatter(logging.Formatter(logformat))
    logging.getLogger().addHandler(ch)
    uh = logging.handlers.DatagramHandler('localhost', 9021)
    uh.setLevel(logging.DEBUG)
    # logging.getLogger().addHandler(uh)
    logger = logging.getLogger('run')
    logger.info('Starting profiling')

    # Load unittest:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('TestSamplesOnVexpress.testBrainFuckQuine', module=test_samples)
    # suite = loader.loadTestsFromName('TestSamplesOnVexpress.testBrainFuckHelloWorld', module=test_samples)
    # suite = loader.loadTestsFromName('TestSamplesOnPython.testBrainFuckQuine', module=test_samples)

    def runtests():
        unittest.TextTestRunner().run(suite)

    p = cProfile.Profile()
    s = p.run('runtests()')
    stats = pstats.Stats(p)
    stats.dump_stats('results.cprofile')
    stats.sort_stats('cumtime')

    # Convert result profile to kcachegrind format:
    if shutil.which('pyprof2calltree'):
        os.system('pyprof2calltree -i results.cprofile')
