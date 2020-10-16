# poseur

[![PyPI - Downloads](https://pepy.tech/badge/python-poseur)](https://pepy.tech/count/python-poseur)
[![PyPI - Version](https://img.shields.io/pypi/v/python-poseur.svg)](https://pypi.org/project/python-poseur)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/python-poseur.svg)](https://pypi.org/project/python-poseur)

[![Travis CI - Status](https://img.shields.io/travis/pybpc/poseur.svg)](https://travis-ci.com/pybpc/poseur)
[![Codecov - Coverage](https://codecov.io/gh/pybpc/poseur/branch/master/graph/badge.svg)](https://codecov.io/gh/pybpc/poseur)
[![Documentation Status](https://readthedocs.org/projects/bpc-poseur/badge/?version=latest)](https://bpc-poseur.readthedocs.io/en/latest/)
<!-- [![LICENSE](https://img.shields.io/badge/license-Anti%20996-blue.svg)](https://github.com/996icu/996.ICU/blob/master/LICENSE) -->

> Write *positional-only parameters* in Python 3.8 flavour, and let `poseur` worry about back-port issues :beer:

&emsp; Since [PEP 570](https://www.python.org/dev/peps/pep-0572/), Python introduced *positional-only parameters*
syntax in version __3.8__. For those who wish to use *positional-only parameters* in their code, `poseur` provides an
intelligent, yet imperfect, solution of a **backport compiler** by replacing *positional-only parameters* syntax with
old-fashioned syntax, which guarantees you to always write *positional-only parameters* in Python 3.8 flavour then
compile for compatibility later.

## Documentation

&emsp; See [documentation](https://bpc-poseur.readthedocs.io/en/latest/) for usage and more details.

## Contribution

&emsp; Contributions are very welcome, especially fixing bugs and providing test cases.
Note that code must remain valid and reasonable.

## See Also

- [`pybpc`](https://github.com/pybpc/bpc) (formerly known as `python-babel`)
- [`f2format`](https://github.com/pybpc/f2format)
- [`walrus`](https://github.com/pybpc/walrus)
- [`vermin`](https://github.com/netromdk/vermin)
