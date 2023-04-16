# seatlib
Library seat watcher for Tsinghua

## install

The only dependencies are `python>=3.9` and `PyYAML` for configurations. However, for cleanliness,
- install [**pipx**](https://pypa.github.io/pipx/) (believe me, it's worth it)
- install [**poetry** with pipx](https://python-poetry.org/docs/#installing-with-pipx) (believe me, it's worth it)
- sync the dependencies with poetry, in a local venv:
```bash
poetry update -vv
```

## config & run

- My personal config is provided as [**prefs.yml**](./prefs.yml)
- To find available library seating areas, see [**areas.yml**](./areas.yml)
- If you are already in a environment with all the dependences, simply run with `./seatlib.py`.
- Otherwise, install and run with poetry:
```bash
poetry run ./seatlib.py
```

## style & `python>=3.9`

As an exercise I try to write pure functions (with no side effects), even though this is expensive in python.
I have hence relied on the dict merge operator `|` introduced in python 3.9.
Ideally all variables are immutable in this script.
