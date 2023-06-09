# seatlib
Library seat watcher for Tsinghua

- This script only _watches_ library areas for available seats.
- It does _**not**_ book the seat for you. That should be done manually.
- Pull requests are very welcomed!

## install

### as a pacakge

- install [**pipx**](https://pypa.github.io/pipx/) (believe me, it's worth it)
- `pipx install git+https://github.com/bryango/seatlib`
- run `seatlib` and see!

<details><summary><h3>as a script</h3></summary>

The only dependencies are:
- `python>=3.9` for the dict merge operator `|`
- `PyYAML` for configurations
- `confuse` (optional) for package config management

If you are already in a environment with all the dependences, simply execute [`./seatlib.py`](./seatlib.py).
However, for cleanliness, it is recommended to:
- install [**pipx**](https://pypa.github.io/pipx/) (believe me, it's worth it)
- install [**poetry** with pipx](https://python-poetry.org/docs/#installing-with-pipx) (believe me, it's worth it)
- install the dependencies with poetry, in a local venv, then run the script:
```bash
## install the latest dependencies
poetry update -vv # --with test,dev  ## for development

## ... alternatively, sync the dependencies locked by `poetry.lock`
poetry install --sync -vv # --with test,dev  ## for development

## finally, run the script
poetry run ./seatlib.py
```

</details>

The script [`./seatlib.py`](./seatlib.py):
- prints its debug output to stderr
- loops until a seat is found, then
- stops and prints the found seat to stdout

This output can be further utilized by a messenger, here realized in the helper script [`./daemon.sh`](./daemon.sh), which notifies the user that a seat is available for manual booking.

## config & run

<details><summary><b>possible conflicts</b></summary><br>

The default config is installed as a stub package [`config`](./config/). This will conflict with [the pypi package of the same name](https://pypi.org/project/config/), but I don't want to rename my config folder, so here it is. If you happens to use the pypi `config`, please install seatlib in a venv without it.

</details>

- when run as a package, the default config is located at `~/.config/seatlib` for linux
- when run as a script, the default config is located at the script directory

The config should be correctly generated at the usual user config directory for all platforms.
The debug printout would show you the config directory. 

- My personal config is provided as [**prefs.yml**](./config/prefs.yml)
- To find available library seating areas, see [**areas.yml**](./config/areas.yml)

## style & `python>=3.9`

As an exercise I try to write pure functions (with no side effects), even though this is expensive in python.
I have hence relied on the dict merge operator `|` introduced in python 3.9.
Ideally all global variables can be made immutable in this script.

## api & spelunking

Firefox provides a nice builtin json viewer that is great for spelunking.

```bash
# curl "https://seat.lib.tsinghua.edu.cn/api.php/v3areas/" > api-dump.json ### this is realized in `seatlib.py`
cat api-dump.json | jq '.data.list.seatinfo | map(select(.name == "文科图书馆")) | .[0].id'
```
