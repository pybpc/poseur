# -*- coding: utf-8 -*-

import os
import re

# root path
ROOT = os.path.dirname(os.path.realpath(__file__))

context = list()
with open(os.path.join(ROOT, 'setup.pypi.py')) as file:
    for line in file:
        match = re.match(r"(?P<prefix>\s*name=').*(?P<suffix>',\s*)", line)
        if match is None:
            context.append(line)
        else:
            context.append('%spython-poseur%s' % (match.group('prefix'), match.group('suffix')))

with open(os.path.join(ROOT, 'setup.pypitest.py'), 'w') as file:
    file.writelines(context)
