#!/usr/bin/env python
# watch for library seats at Tsinghua

# %%
SLEEP_INTERVAL = [10, 20]   # pause between refreshes
AREAS_YML = './areas.yml'   # export: valid areas
PREFS_YML = './prefs.yml'   # input:  preferred areas
API_TSINGHUA_SEATLIB = 'https://seat.lib.tsinghua.edu.cn/api.php/v3areas'
API_DUMP_JSON = './api-dump.json'

import sys
import signal
import time
import urllib.request
import json
import random
import yaml


# %% debugging utilities
def eprint(*args, **kwargs):
    """ prints to stderr by default """
    kwargs.setdefault('file', sys.stderr)
    kwargs.setdefault('sep', '\t')
    print(*args, **kwargs)

def timestamp(fullform=False):
    return time.asctime() if fullform else time.asctime().split()[-2]

eprint(timestamp(), 'starting seat watcher for Tsinghua libraries...')

### suppress KeyboardInterrupt
signal.signal(
    signal.SIGINT,
    lambda signal_number, current_stack_frame: sys.exit(0)
)


# %% load and process preferences
def canonicalize(tree):
    """ rewrites the `prefs.yml` tree as a nested dict, recursively """

    if type(tree) is dict:
        # key is always canonicalize to a string
        return { str(key): canonicalize(value) for key, value in tree.items() }

    if type(tree) is list:
        newtree = {}
        for entry in tree:
            if type(entry) is dict:
                newtree |= {
                    str(key): canonicalize(value)
                    for key, value in entry.items()
                    if key not in newtree  # skip specified keys
                }
            else:
                newtree |= canonicalize(entry)
        return newtree

    if tree is None:
        return 0

    if type(tree) is str:
        tree = tree.strip()
        if tree.startswith('^'):
            return int(tree.lstrip('^'))

    return { str(tree): 0 }


with open(PREFS_YML) as datafile:
    prefs_tree = yaml.safe_load(datafile)

eprint('preferences:', prefs_tree)
prefs_tree = canonicalize(prefs_tree)
eprint('canonicalized:', prefs_tree)


# %% load and process dataset from api
def load_dataset(
    api_url: str = API_TSINGHUA_SEATLIB,
    api_dumpfile: str = API_DUMP_JSON
):
    """ load data from API and dump to `api-dump.json`, returning seatinfo """
    with urllib.request.urlopen(api_url) as response:
        data = response.read()
    with open(api_dumpfile, 'wb') as dumpfile:
        dumpfile.write(data)
    return json.loads(data)['data']['list']['seatinfo']


def select_matching(listdicts: list[dict], key, value):
    return [ entry for entry in listdicts if entry[key] == value ]


def adopt_areas(dataset: list[dict], parents: list[dict]):
    """ adopt child areas from the dataset, for each of the parents """
    families = []
    for this_parent in parents:
        children = select_matching(dataset, 'parentId', this_parent['id'])
        families.append(
            this_parent | {
                'children': adopt_areas(dataset, parents=children)
            }
        )
    return families


dataset = load_dataset()
godmother = { 'id': 0 }
libraries = select_matching(dataset, 'parentId', godmother['id'])
families_tree = adopt_areas(dataset, libraries)


# %% write available areas to `areas.yml`
def family_names(families: list[dict], grandparent: dict = {}):
    """ generates a nested dict of family names """
    return {
        family['name'].strip(): family_names(
            families=family['children'],
            grandparent=family
        )
        for family in families
    } or grandparent['TotalCount']  # at the end / leaf of the family tree


with open(AREAS_YML, 'w') as areafile:
    areafile.write('\n'.join([
        line.strip() for line in f"""\
            # available library sub-areas, with number of spaces
            # this file is generated automatically by `seatlib.py`
            # at: {timestamp(fullform=True)}
        \n""".splitlines()
    ]))
    yaml.safe_dump(
        family_names(families_tree),
        stream=areafile,
        allow_unicode=True,
        encoding='utf-8'
    )


# %%
def eprint_info(site_info: dict, timeline: bool = True, **kwargs):
    if timeline:
        eprint(timestamp(), end='\t')
    eprint(f"{site_info['id']}",
           f"{site_info['AvailableSpace']}/{site_info['TotalCount']}",
           f"{site_info['name']}",
           **kwargs)


def match_areas(selectors: dict, areas: list[dict], parent_name: str = ''):
    """ match areas to area selectors, recursively """

    for site in areas:

        matched_keys = [ key for key in selectors if key in site['name'] ]
        if not any(matched_keys):
            continue

        site_info = {
            'name': ' '.join([ parent_name, site['name'].strip() ]).strip(),
            'TotalCount': site['TotalCount'],
            'AvailableSpace': site['TotalCount'] - site['UnavailableSpace'],
            'id': site['id']
        }

        next_selectors = selectors[matched_keys[0]]
        if type(next_selectors) is int:  # at the end / leaf of the family tree

            minimal_seatnum = next_selectors
            eprint_info(site_info)
            if site_info['AvailableSpace'] > minimal_seatnum:
                return site_info

            continue  # no return if none available

        next_areas = site['children']
        next_match = match_areas(next_selectors, next_areas, site_info['name'])
        if next_match:
            return next_match
        continue


def watch(prefs_tree, pause: list = SLEEP_INTERVAL):
    with urllib.request.urlopen(API_TSINGHUA_SEATLIB) as datafile:
        dataset = json.load(datafile)['data']['list']['seatinfo']

    libraries = select_matching(dataset, 'parentId', godmother['id'])
    families = adopt_areas(dataset, libraries)

    hit = match_areas(prefs_tree, families)
    if hit:
        eprint_info(hit, timeline=False, file=sys.stdout)
        return hit

    time.sleep(random.uniform(*SLEEP_INTERVAL))
    return watch(prefs_tree, pause=pause)


if __name__ == '__main__':
    watch(prefs_tree)
