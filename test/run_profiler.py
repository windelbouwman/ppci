
import cProfile
import unittest
import pstats
import testsamples
import logging

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logformat='%(asctime)s|%(levelname)s|%(name)s|%(message)s'
    ch.setFormatter(logging.Formatter(logformat))
    logging.getLogger().addHandler(ch)
    logger = logging.getLogger('run')
    logger.info('Starting profiling')
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('TestSamplesOnVexpress.testBrainFuckHelloWorld', module=testsamples)
    def runtests():
        unittest.TextTestRunner().run(suite)
    #s = cProfile.run('runtests()',sort='cumtime')
    p = cProfile.Profile()
    s = p.run('runtests()')
    stats = pstats.Stats(p)
    #stats.sort_stats('tottime')
    stats.sort_stats('cumtime')
    stats.print_stats(.1)
