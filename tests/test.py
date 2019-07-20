# -*- coding: utf-8 -*-

import os
import sys
import tempfile
import unittest

from poseur import get_parser, poseur


class TestPoseur(unittest.TestSuite):

    def test_get_parser(self):
        parser = get_parser()
        args = parser.parse_args(['-n', '-q', '-p/tmp/',
                                  '-cgb2312', '-v3.6',
                                  'test1.py', 'test2.py'])

        self.assertIs(args.quiet, True,
                      'run in quiet mode')
        self.assertIs(args.no_archive, True,
                      'do not archive original files')
        self.assertEqual(args.archive_path, '/tmp/',
                         'path to archive original files')
        self.assertEqual(args.encoding, 'gb2312',
                         'encoding to open source files')
        self.assertEqual(args.python, '3.6',
                         'convert against Python version')
        self.assertEqual(args.file, ['test1.py', 'test2.py'],
                         'python source files and folders to be converted')

    def test_poseur(self):
        pass
