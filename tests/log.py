#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0
Logging handler for my projects """

import os
import sys
import logging

# pylint: disable=invalid-name
log_file_global = None
encoding_global = None
# pylint: enable=invalid-name

# Configure logging to emit messages via 'print' method
class LoggingHandler(logging.Handler):
    """Logging to local file."""

    def __init__(self, log_file:str=None, encoding:str=None):
        super().__init__()

        if log_file is None:
            raise NameError(name = 'None')

        # pylint: disable=global-statement
        global log_file_global
        log_file_global = log_file
        global encoding_global
        encoding_global = encoding
        # pylint: enable=global-statement

        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        # Remove old log file
        if os.path.isfile(log_file_global):
            os.remove(log_file_global)

    def emit(self, record):
        print_logfile_line(self.format(record))


# Redefine print method to write logs to file
def print_logfile_line(*args):
    """Print a line into the local log file."""
    line = ' '.join([str(arg) for arg in args])
    line = line.rstrip() + '\n'
    # pylint: disable=global-variable-not-assigned
    global log_file_global
    global encoding_global
    # pylint: enable=global-variable-not-assigned

    with open(log_file_global, 'a', encoding = encoding_global) as f:
        f.write(line)
    sys.stdout.write(line)


def read_and_log(stdout):
    """Infinite cycle to read process'es stdout."""

    while True:
        line = stdout.readline()
        if os.name == 'nt':
            line = line.replace(b'\x0c', b'') # clear screen Windows
            line = line.replace(b'\r', b'') # \n Windows
        else:
            line = line.replace(b'\x1b[H\x1b[2J\x1b[3J', b'') # clear screen Linux
        if line != b'':
            line = line.decode().rstrip()
            print_logfile_line(line)
        else:
            break
