![StaticBadge](https://img.shields.io/badge/support-ACTIVE-green)

[![License](https://img.shields.io/github/license/mausy5043/mausy5043-common)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/mausy5043-common.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/mausy5043-common)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/mausy5043-common.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/mausy5043-common)
[![PyPI downloads](https://img.shields.io/pypi/dm/mausy5043-common.svg)](https://pypistats.org/packages/mausy5043-common)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-008800.svg)](https://github.com/astral-sh/ruff)
[![Linter: ruff](https://img.shields.io/badge/linter-ruff-008800.svg)](https://github.com/astral-sh/ruff)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Mausy5043/mausy5043-common/devel.svg)](https://results.pre-commit.ci/latest/github/Mausy5043/mausy5043-common/devel)
[![Dependabot Updates](https://github.com/Mausy5043/mausy5043-common/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/Mausy5043/mausy5043-common/actions/workflows/dependabot/dependabot-updates)

# mausy5043-common

This is a Python3 library of functions and classes, mainly for personal use.

## Requirements

**NOTE: user action required !!**
Before trying to use the SQLITE3 functions in this package make sure you have installed the sqlite3 server/client and
the default Python package that comes with it.

Development of this package is done in Python 3.12. Backwards compatibility is not tested; if it works on Python 3.7 or before consider yourself lucky. [Python versions that are end-of-life](https://devguide.python.org/versions/) are not supported.

## Installation

```
python3 -m pip install mausy5043-common
```


## Functions provided
`cat(filename)` : Read a file into a variable.
`moisture(temperature, relative_humidity, pressure)` : Calculate the moisture content of air given T [degC], RH [%] and P [hPa].
`wet_bulb_temperature(temperature, relative_humidity)` : Calculate the wet bulb temperature of the air given T [degC] and RH [%].

## Classes provided
`SqlDatabase` : A class to interact with SQLite3 databases.

## Disclaimer & License
As of September 2024 `mausy5043-common` is distributed under [AGPL-3.0-or-later](LICENSE).
