# poseur

[![PyPI - Downloads](https://pepy.tech/badge/poseur)](https://pepy.tech/count/poseur)
[![PyPI - Version](https://img.shields.io/pypi/v/poseur.svg)](https://pypi.org/project/poseur)
[![PyPI - Format](https://img.shields.io/pypi/format/poseur.svg)](https://pypi.org/project/poseur)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/poseur.svg)](https://pypi.org/project/poseur)

[![Travis CI - Status](https://travis-ci.com/JarryShaw/poseur.svg)](https://travis-ci.org/JarryShaw/poseur)
[![Codecov - Coverage](https://codecov.io/gh/JarryShaw/poseur/branch/master/graph/badge.svg)](https://codecov.io/gh/JarryShaw/poseur)
![License](https://img.shields.io/github/license/jarryshaw/poseur.svg)
[![LICENSE](https://img.shields.io/badge/license-Anti%20996-blue.svg)](https://github.com/996icu/996.ICU/blob/master/LICENSE)

 > Write *positional-only parameters* in Python 3.8 flavour, and let `poseur` worry about back-port issues :beer:

&emsp; Since [PEP 570](https://www.python.org/dev/peps/pep-0570/), Python introduced *positional-only parameters*
syntax in version __3.8__. For those who wish to use *positional-only parameters* in their codes, `poseur` provides an
intelligent, yet imperfect, solution of a **backport compiler** by removing *positional-only parameters* syntax whilst
introduce a *decorator* for runtime checks, which guarantees you to always write *positional-only parameters* in Python
3.8 flavour then compile for compatibility later.

## Installation

> Note that `poseur` only supports Python versions __since 3.3__ 🐍

&emsp; For macOS users, `poseur` is now available through [Homebrew](https://brew.sh):

```sh
brew tap jarryshaw/tap
brew install poseur
# or simply, a one-liner
brew install jarryshaw/tap/poseur
```

&emsp; Simply run the following to install the current version from PyPI:

```sh
pip install poseur
```

&emsp; Or install the latest version from the git repository:

```sh
git clone https://github.com/JarryShaw/poseur.git
cd poseur
pip install -e .
# and to update at any time
git pull
```

## Basic Usage

### CLI

&emsp; It is fairly straightforward to use `poseur`:

 > context in `${...}` changes dynamically according to runtime environment

```man
usage: poseur [options] <python source files and folders...>

Convert f-string to str.format for Python 3 compatibility.

positional arguments:
  SOURCE                python source files and folders to be converted (${CWD})

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -q, --quiet           run in quiet mode

archive options:
  duplicate original files in case there's any issue

  -n, --no-archive      do not archive original files
  -p PATH, --archive-path PATH
                        path to archive original files (${CWD}/archive)

convert options:
  compatibility configuration for none-unicode files

  -c CODING, --encoding CODING
                        encoding to open source files (${LOCALE_ENCODING})
  -v VERSION, --python VERSION
                        convert against Python version (${LATEST_VERSION})
  -s SEP, --linesep SEP
                        line separator to process source files (${OS_LINESEP})
  -d, --dismiss         dismiss runtime checks for positional-only parameters
  -nl, --no-linting     do not lint converted codes
  -r VAR, --decorator VAR
                        name of decorator for runtime checks (${DECORATOR})

```

&emsp; `poseur` will read then convert all *positional-only parameters* syntax in every Python
file under this path. In case there might be some problems with the conversion, `poseur` will
duplicate all original files it is to modify into `archive` directory ahead of the process,
if `-n` not set.

&emsp; Besides, to keep consistency of API to users, `poseur` ships with a *decorator* for
such functions to check positional-only parameters at runtime, if `-nl` not set.

## Developer Reference

### Environments

`poseur` currently supports three environment arguments:

- `POSEUR_QUIET` -- run in quiet mode (same as `--quiet` option in CLI)
- `POSEUR_VERSION` -- convert against Python version (same as `--python` option in CLI)
- `POSEUR_ENCODING` -- encoding to open source files (same as `--encoding` option in CLI)
- `POSEUR_LINESEP` -- line separator to process source files (same as `--linesep` option in CLI)
- `POSEUR_DISMISS` -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
- `POSEUR_LINTING` -- lint converted codes (same as `--linting` option in CLI)
- `POSEUR_DECORATOR` -- name of decorator for runtime checks (same as `--decorator` option in CLI)

### APIs

#### `poseur` -- wrapper works for conversion

```python
poseur(filename)
```

Args:

- `filename` -- `str`, file to be converted

Envs:

- `POSEUR_QUIET` -- run in quiet mode (same as `--quiet` option in CLI)
- `POSEUR_ENCODING` -- encoding to open source files (same as `--encoding` option in CLI)
- `POSEUR_VERSION`-- convert against Python version (same as `--python` option in CLI)
- `POSEUR_LINESEP` -- line separator to process source files (same as `--linesep` option in CLI)
- `POSEUR_DISMISS` -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
- `POSEUR_LINTING` -- lint converted codes (same as `--linting` option in CLI)
- `POSEUR_DECORATOR` -- name of decorator for runtime checks (same as `--decorator` option in CLI)

Raises:

- `ConvertError `-- when `parso.ParserSyntaxError` raised

#### `convert` -- the main conversion process

```python
convert(string, source='<unknown>')
```

Args:

- `string` -- `str`, context to be converted
- `source` -- `str`, source of the context

Envs:

- `POSEUR_VERSION`-- convert against Python version (same as `--python` option in CLI)
- `POSEUR_LINESEP` -- line separator to process source files (same as `--linesep` option in CLI)
- `POSEUR_DISMISS` -- dismiss runtime checks for positional-only arguments (same as `--dismiss` option in CLI)
- `POSEUR_LINTING` -- lint converted codes (same as `--linting` option in CLI)
- `POSEUR_DECORATOR` -- name of decorator for runtime checks (same as `--decorator` option in CLI)

Returns:

- `str` -- converted string

Raises:

- `ConvertError `-- when `parso.ParserSyntaxError` raised

#### `ConvertError` -- `poseur` internal exception

```python
class ConvertError(SyntaxError):
    pass
```

## Test

&emsp; See [`test.py`](https://github.com/JarryShaw/poseur/blob/master/scripts/test.py).

## Contribution

&emsp; Contributions are very welcome, especially fixing bugs and providing test cases.
Note that code must remain valid and reasonable.

## See Also

- [`babel`](https://github.com/jarryshaw/babel)
- [`f2format`](https://github.com/jarryshaw/f2format)
- [`walrus`](https://github.com/jarryshaw/walrus)
- [`vermin`](https://github.com/netromdk/vermin)
