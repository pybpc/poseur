# NB: poseur is currently under reconstruction. It is highly recommended to directly install from the git repo or the pre-release distributions.

---

# poseur

[![PyPI - Version](https://img.shields.io/pypi/v/bpc-poseur.svg)](https://pypi.org/project/bpc-poseur)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bpc-poseur.svg)](https://pypi.org/project/bpc-poseur)

[![GitHub Actions - Status](https://github.com/pybpc/bpc-poseur/workflows/Build/badge.svg)](https://github.com/pybpc/bpc-poseur/actions?query=workflow%3ABuild)
[![Codecov - Coverage](https://codecov.io/gh/pybpc/bpc-poseur/branch/master/graph/badge.svg)](https://codecov.io/gh/pybpc/bpc-poseur)
[![Documentation Status](https://readthedocs.org/projects/bpc-poseur/badge/?version=latest)](https://bpc-poseur.readthedocs.io/en/latest/)

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
- [`relaxedecor`](https://github.com/pybpc/relaxedecor)
- [`vermin`](https://github.com/netromdk/vermin)
