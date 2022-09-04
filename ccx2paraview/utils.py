#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" © Ihor Mirzov, 2019-2022
Distributed under GNU General Public License v3.0

Some utility functions for ccx2paraview. """

import logging


def print_some_log(b, results_counter=None):
    """b is a results block."""
    if results_counter is None:
        results_counter = len(b.results)
    if b.value < 1:
        time_str = 'time {:.2e}, '.format(b.value)
    else:
        time_str = 'time {:.1f}, '.format(b.value)
    txt = 'Step {}, '.format(b.numstep) + time_str \
        + '{}, '.format(b.name) \
        + '{} components, '.format(len(b.components)) \
        + '{} values'.format(results_counter)
    logging.info(txt)
