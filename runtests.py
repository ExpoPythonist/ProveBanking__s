#!/usr/bin/env python
import os
import sys
import argparse
import cProfile
from argparse import RawTextHelpFormatter

import pytest


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))


def exit_on_failure(ret, message=None):
    if ret:
        sys.exit(ret)


description = """
Run unit tests for Proven.

Usage: ./runtests.py [--ds=med_social.settings] [options py.test]
"""


parser = argparse.ArgumentParser(description=description, formatter_class=RawTextHelpFormatter)
parser.add_argument('--ds', metavar='settings', default='med_social.settings.test',
                    help='Django settings')


if __name__ == '__main__':
    args = sys.argv[1:]

    parsed, pytest_arguments = parser.parse_known_args(args)

    pytest_arguments.append('--nomigrations')
    pytest_arguments.extend(['--ds', parsed.ds])

    path_to_run = ['./apps', './med_social']

    pytest_arguments = path_to_run + pytest_arguments

    ret_code = pytest.main(pytest_arguments)

    exit_on_failure(ret_code)
