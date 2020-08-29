#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2020
Distributed under GNU General Public License v3.0
Logging handler for all my projects """

import os
import sys
import logging


log_file = os.path.join(os.path.dirname(__file__), 'test.log')


# Configure logging to emit messages via 'print' method
class myHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        # Remove old log file
        if os.path.isfile(log_file):
            os.remove(log_file)

    def emit(self, LogRecord):
        print(self.format(LogRecord))


# Redefine print method to write logs to file
def print(*args):
    line = ' '.join([str(arg) for arg in args])
    line = line.rstrip() + '\n'
    with open(log_file, 'a') as f:
        f.write(line)
    sys.stdout.write(line)


# Infininte cycle to read process'es stdout
def read_and_log(stdout):
    while True:
        line = stdout.readline()
        if os.name == 'nt':
            line = line.replace(b'\x0c', b'') # clear screen Windows
            line = line.replace(b'\r', b'') # \n Windows
        else:
            line = line.replace(b'\x1b[H\x1b[2J\x1b[3J', b'') # clear screen Linux
        if line != b'':
            line = line.decode().rstrip()
            print(line)
        else:
            break
