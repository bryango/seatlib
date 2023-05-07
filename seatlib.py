#!/usr/bin/env python
# watch for library seats at Tsinghua

# %% setup & paths
SLEEP_INTERVAL = [10, 20]       # pause between refreshes
AREAS_YML : str = 'areas.yml'   # output: valid areas
PREFS_YML : str = 'prefs.yml'   # input:  preferred areas
HATES_YML : str = 'hates.yml'   # input:  hated areas
CONFIG_DIR_DEFAULT : str = 'config'

API_DUMP_AREAS = './api-areas.json'
API_DUMP_SEATCODES = './api-seatcodes.json'
API_TSINGHUA_AREAS = 'https://seat.lib.tsinghua.edu.cn/api.php/v3areas'
API_TSINGHUA_DAYS = 'https://seat.lib.tsinghua.edu.cn/api.php/v3areadays'
API_TSINGHUA_SEATCODES = 'https://seat.lib.tsinghua.edu.cn/api.php/spaces_old'

import os
import sys
import signal
import time
import urllib.request
import json
import random
import functools
import operator
import enum
import fnmatch
import yaml

### set working directory
## $ cd "$(dirname "$(readlink -f "$0")")"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

### suppress KeyboardInterrupt
signal.signal(
    signal.SIGINT,
    lambda signal_number, current_stack_frame: sys.exit(0)
)


# %% debugging utilities
def eprint(*args, **kwargs):
    """ prints to stderr by default """
    kwargs.setdefault('file', sys.stderr)
    kwargs.setdefault('sep', '\t')
    print(*args, **kwargs)

def timestamp(fullform=False):
    return time.asctime() if fullform else time.asctime().split()[-2]

eprint(
    timestamp(),
    f'starting seat watcher for Tsinghua libraries as `{__name__}`...'
)
eprint()


# %% config discovery

## initialize CONFIG_DIR
CONFIG_DIR : str = CONFIG_DIR_DEFAULT

## update CONFIG_DIR
if __name__ != '__main__':  # the script is imported:
    try:  # cross platform config management
        import confuse
        CONFIG_DIR = confuse.Configuration('seatlib', modname=__name__) \
                            .config_dir()
    except ModuleNotFoundError:
        CONFIG_DIR = os.path.expanduser('~/.config/seatlib')

CONFIG_DIR = os.path.abspath(CONFIG_DIR)
eprint('config dir:', CONFIG_DIR)


def find_config(yml_config: str) -> str:
    """ find and return config path, creating a default if non-existed """
    config_path = os.path.join(CONFIG_DIR, yml_config)
    if not os.path.exists(config_path):
        import shutil
        config_path_default = os.path.join(CONFIG_DIR_DEFAULT, yml_config)
        shutil.copy2(config_path_default, config_path)

    return config_path


# %% process preferences
def canonicalize_prefs(tree):
    """ rewrites the `prefs.yml` tree as a nested dict, recursively """

    if type(tree) is dict:
        # key is always canonicalize to a string
        return {
            str(key): canonicalize_prefs(value)
            for key, value in tree.items()
        }

    if type(tree) is list:
        newtree = {}
        for entry in tree:
            if type(entry) is dict:
                newtree |= {
                    str(key): canonicalize_prefs(value)
                    for key, value in entry.items()
                    if key not in newtree  # skip specified keys
                }
            else:
                newtree |= canonicalize_prefs(entry)
        return newtree

    if tree is None:
        return 0

    if type(tree) is str:
        tree = tree.strip()
        if tree.startswith('^'):
            return int(tree.lstrip('^'))

    return { str(tree): 0 }


def load_prefs():
    with open(find_config(PREFS_YML), 'r') as datafile:
        prefs_tree = yaml.safe_load(datafile)

    eprint('preferences:', prefs_tree)
    prefs_tree = canonicalize_prefs(prefs_tree)
    eprint('canonicalized:', prefs_tree)

    return prefs_tree


def load_hatelist() -> list[str]:
    hatelist_path = find_config(HATES_YML)
    with open(hatelist_path, 'r') as datafile:
        hatelist : list[str] = yaml.safe_load(datafile)
        eprint('block list:', hatelist_path)
    return hatelist


hatelist = load_hatelist()
prefs_tree = load_prefs()
eprint()


# %% load dataset from api
def load_dataset(
    api_url: str = API_TSINGHUA_AREAS,
    selectors: list[str | int] = ['data', 'list', 'seatinfo'],
    api_dump_path: str = ''
):
    """ load data from API and return a selected subset """
    with urllib.request.urlopen(api_url) as response:
        data = response.read()
    if api_dump_path:
        with open(api_dump_path, 'wb') as datafile:
            datafile.write(data)

    # nested dict access: https://stackoverflow.com/a/14692747
    return functools.reduce(operator.getitem, selectors, json.loads(data))


def select_matching(listdicts: list[dict], key, value) -> list:
    return [ entry for entry in listdicts if entry[key] == value ]


def select_children(dataset: list[dict], parent_id: int = 0) -> list:
    """ select children by `parentId`, which defaults to 0 at top level """
    return select_matching(dataset, 'parentId', parent_id)


def adopt_children(dataset: list[dict], parents: list[dict]):
    """ adopt children from the dataset, for each of the parents """
    families = []
    for this_parent in parents:
        children = select_children(dataset, this_parent['id'])
        families.append(
            this_parent | {
                'children': adopt_children(dataset, parents=children)
            }
        )
    return families


def assemble_families(api_dump_path: str = ''):
    """ organize available areas as a tree of families """
    dataset = load_dataset(api_dump_path=api_dump_path)
    libraries = select_children(dataset)
    return adopt_children(dataset, libraries)


family_tree = assemble_families(api_dump_path=API_DUMP_AREAS)


# %% export available areas
def families_names(families: list[dict], grandparent: dict = {}):
    """ generates a nested dict of family names """
    return {
        family['name'].strip(): families_names(
            families=family['children'],
            grandparent=family
        )
        for family in families
    } or grandparent['TotalCount']  # at the end / leaf of the family tree


areas_tree = families_names(family_tree)

def dump_areas():
    with open(find_config(AREAS_YML), 'w') as datafile:
        datafile.write('\n'.join([
            line.strip() for line in f"""\
                # available library sub-areas, with available spaces
                # this file is generated automatically by `seatlib.py`
                # at: {timestamp(fullform=True)}
            \n""".splitlines()
        ]))
        yaml.safe_dump(
            areas_tree,
            stream=datafile,
            allow_unicode=True,
            encoding='utf-8'
        )

dump_areas()


# %% filter hate list TODO
def fetch_day_data(area_id: int):
    return load_dataset(
        f"{API_TSINGHUA_DAYS.rstrip('/')}/{area_id}",
        ['data', 'list', 0]
    )

def load_seatcodes(area_id: int):
    day_data = fetch_day_data(area_id)
    time_data = {
        ## "2023-05-06 08:00:00" -> "08:00:00"
        key: day_data[key]['date'].split(' ')[-1]
        for key in ('startTime', 'endTime')
    }
    time_data = time_data | {
        ## actually, use _now_ as the the 'startTime'
        'startTime': timestamp()
    }
    return load_dataset(
        f"{API_TSINGHUA_SEATCODES.rstrip('/')}?"
        f"area={day_data['area']}&"
        f"segment={day_data['id']}&"
        f"day={day_data['day']}&"
        f"startTime={time_data['startTime']}&"
        f"endTime={time_data['endTime']}",
        ['data', 'list'],
        API_DUMP_SEATCODES
    )


class SeatStat(enum.IntEnum):
    AVAILABLE  = 1
    IN_USE     = 6
    TEMP_LEAVE = 7


def select_seats(seats: list[dict], status: SeatStat = SeatStat.AVAILABLE):
    return select_matching(seats, 'status', status)


# seats: list[dict] = load_seatcodes(95)
# focused_seats = select_seats(seats, SeatStat.TEMP_LEAVE)
# focused_codes = [ seat['name'] for seat in focused_seats ]
# focused_codes


def match_seat(hatelist: list[str], seat: dict):
    """ match a seat to the rules in the hatelist """
    matched_hates = [
        rule for rule in hatelist
        if fnmatch.fnmatch(seat['name'], rule)
    ]
    # eprint(matched_hates)
    return matched_hates


def exclude_seats(hatelist: list[str], seats: list[dict]):
    """ exclude seats in the hatelist """
    return [
        site for site in seats
        if not match_seat(hatelist, site)
    ]


# exclude_seats(hatelist, focused_seats)



# %% find selected areas
def eprint_info(site_info: dict, **kwargs):
    eprint(timestamp(),
           f"{site_info['id']}",
           f"{site_info['AvailableSpace']}/{site_info['TotalCount']}",
           f"{site_info['name']}",
           **kwargs)


def match_areas(
        selectors: dict,
        areas: list[dict],
        parent_name: str = ''
) -> dict:
    """ match areas to area selectors, recursively """

    for site in areas:

        matched_keys = [ key for key in selectors if key in site['name'] ]
        if not matched_keys:
            continue

        site_info = {
            'name': ' '.join([ parent_name, site['name'].strip() ]).strip(),
            'TotalCount': site['TotalCount'],
            'AvailableSpace': site['TotalCount'] - site['UnavailableSpace'],
            'id': site['id']
        }

        next_selectors : dict|int = selectors[matched_keys[0]]

        if type(next_selectors) is dict: # recurse into the next level
            next_areas = site['children']
            next_match = match_areas(
                next_selectors,
                next_areas,
                site_info['name']
            )
            if not next_match:
                continue  # to the next site
            return next_match

        if type(next_selectors) is int: # at the end / leaf of the family tree
            minimal_seatnum : int = next_selectors
            eprint_info(site_info)
            if site_info['AvailableSpace'] <= minimal_seatnum:
                continue  # to the next site
            return site_info

    return {}  # if no match


# %% watch the api
def watch(
        prefs_tree,
        pause: list = SLEEP_INTERVAL,
        print_header: bool = True
) -> dict:

    if print_header:
        eprint_info({
            'id': 'id',
            'name': 'name',
            'AvailableSpace': '👌',
            'TotalCount': '👇'
        })

    # reload dataset
    family_tree = assemble_families()

    hit = match_areas(prefs_tree, family_tree)
    if hit:
        eprint_info(hit, file=sys.stdout)
        return hit

    time.sleep(random.uniform(*SLEEP_INTERVAL))
    return watch(prefs_tree, pause=pause, print_header=False)


def execute() -> None:
    """ provide the script entry point, always return None """
    watch(prefs_tree)


if __name__ == '__main__':
    execute()
