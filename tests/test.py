# -*- coding: utf-8 -*-
# pylint: disable=no-member

import os
import sys
import tempfile
import unittest

from poseur import decorator, get_parser, poseur

# root path
ROOT = os.path.dirname(os.path.realpath(__file__))


class TestPoseur(unittest.TestSuite):

    def test_get_parser(self):
        parser = get_parser()
        args = parser.parse_args(['-na', '-q', '-p/tmp/',
                                  '-cgb2312', '-v3.6',
                                  'test1.py', 'test2.py'])

        self.assertIs(args.quiet, True,
                      'run in quiet mode')
        self.assertIs(args.archive, False,
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
        with open(os.path.join(ROOT, 'sample', 'new.py')) as file:
            old = file.read()

        with tempfile.TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, 'test.py')
            with open(path, 'w') as file:
                file.write(old)
            poseur(path)


if __name__ == '__main__':
    sys.exit(unittest.main())
