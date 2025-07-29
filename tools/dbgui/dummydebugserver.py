#!/usr/bin/python

from ppci.dbg import DummyDebugServer

if __name__ == "__main__":
    server = DummyDebugServer()
    server.serve()
