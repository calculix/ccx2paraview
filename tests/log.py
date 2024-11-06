#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" 
© Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0
Logging handler for my projects 

soylentOrange: Updated for testing simulation and converter using different filenames for the log
"""

import os
import sys
import logging

# Configure logging
class LoggingHandler(logging.Handler):
    """Logging to local file."""

    def __init__(self, log_file:str=None, encoding:str=None):
        super().__init__()

        if log_file is None:
            raise ValueError('No log-file name given!')

        self.log_file = log_file
        self.encoding = encoding
        self.monitor_stdout = True

        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

        # Remove old log file
        if os.path.isfile(self.log_file):
            os.remove(self.log_file)

    def emit(self, record):
        self.println(self.format(record))

    def println(self, *args):
        """Print a line into the local log file."""
        line = ' '.join([str(arg) for arg in args])
        line = line.rstrip() + '\n'
        with open(self.log_file, 'a', encoding = self.encoding) as f:
            f.write(line)
        sys.stdout.write(line)

    def stop_read_and_log(self):
        """Stop cycle to read process'es stdout."""
        self.monitor_stdout = False

    def read_and_log(self, stdout):
        """Semi-Infinite cycle to read process'es stdout."""

        while self.monitor_stdout:
            line = stdout.readline()
            if os.name == 'nt':
                line = line.replace(b'\x0c', b'') # clear screen Windows
                line = line.replace(b'\r', b'') # \n Windows
            else:
                line = line.replace(b'\x1b[H\x1b[2J\x1b[3J', b'') # clear screen Linux
            if line != b'':
                line = line.decode().rstrip()
                self.println(line)
            else:
                break
