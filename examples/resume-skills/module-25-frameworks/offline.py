"""Fail if these fixtures attempt an external socket connection."""
import sys


def guard_external_connections():
    attempts = []

    def audit(event, args):
        if event != 'socket.connect':
            return
        address = args[1]
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1', 'localhost'):
            attempts.append(str(address))
            raise RuntimeError('External network disabled for framework fixtures')

    sys.addaudithook(audit)
    return attempts
