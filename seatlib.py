#!/usr/bin/env python

# %%
import json
import urllib.request
import random
import time
import sys
import yaml


# %%
def eprint(*args, **kwargs):
    """ prints to stderr by default """
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)


def timestamp():
    eprint(time.asctime().split()[-2], end='\t')


timestamp()
eprint()


# %%
def canonicalize(tree, flatten=True):
    """ rewrites a yaml tree as a nested dict, recursively """

    if tree is None:
        return {}

    if all(type(tree) is not x for x in [list, dict]):
        return { str(tree): {} }

    if type(tree) is dict:
        return { key: canonicalize(value) for key, value in tree.items() }

    if type(tree) is list:
        newtree = {}
        for entry in tree:
            if type(entry) is dict:
                newtree |= {
                        key: canonicalize(value)
                        for key, value in entry.items()
                        if key not in newtree  # skip specified keys
                    }
            else:
                newtree |= canonicalize(entry)
        return newtree


with open('./prefs.yml') as datafile:
    target_tree = yaml.safe_load(datafile)

eprint('preferences:', target_tree, sep='\t')
target_tree = canonicalize(target_tree)
eprint('canonicalized:', target_tree, sep='\t')

# %%
SEAT_LIB_TSINGHUA = 'https://seat.lib.tsinghua.edu.cn/api.php/v3areas'
SLEEP_INTERVAL = [10, 20]


# %%
def select_matching(listdicts, key, value):
    return [ entry for entry in listdicts if entry[key] == value ]


# %%
def adopt_areas(dataset: list, parents: list):
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


with urllib.request.urlopen(SEAT_LIB_TSINGHUA) as datafile:
    dataset = json.load(datafile)['data']['list']['seatinfo']

godmother = { 'id': 0 }
libraries = select_matching(dataset, 'parentId', godmother['id'])
families = adopt_areas(dataset, libraries)


# %%
def family_names(families: list, grandparent: dict = {}):
    """ generates a nested dict of family names """
    return {
        family['name'].strip(): family_names(
            families=family['children'],
            grandparent=family
        )
        for family in families
    } or grandparent['TotalCount']  # for end of the leaf


with open('./areas.yml', 'w') as areafile:
    areafile.write('\n'.join([
        line.strip() for line in """\
            # available library areas, with number of spaces
            # this file is generated automatically by `seatlib.py`
        \n""".splitlines()
    ]))
    yaml.dump(
        family_names(families),
        stream=areafile,
        allow_unicode=True,
        encoding='utf-8'
    )


# %%
def recursive_match(selectors, areas: list, parent_name: str = ''):

    for site in areas:

        matched_keys = [ key for key in selectors if key in site['name'] ]
        if not any(matched_keys):
            continue

        site_info = {
            'name': ' '.join([ parent_name, site['name'].strip() ]).strip(),
            'TotalCount': site['TotalCount'],
            'AvailableSpace': site['TotalCount'] - site['UnavailableSpace']
        }

        next_selectors = selectors[matched_keys[0]]
        if not next_selectors:  # end of the leaf
            timestamp()
            eprint(site_info)

            if site_info['AvailableSpace']:
                return site_info

            continue  # no return if none available

        next_areas = site['children']
        return recursive_match(next_selectors, next_areas, site_info['name'])


def watch(target_tree):
    with urllib.request.urlopen(SEAT_LIB_TSINGHUA) as datafile:
        dataset = json.load(datafile)['data']['list']['seatinfo']

    libraries = select_matching(dataset, 'parentId', godmother['id'])
    families = adopt_areas(dataset, libraries)

    hit = recursive_match(target_tree, families)
    if hit:
        return hit

    time.sleep(random.uniform(*SLEEP_INTERVAL))
    return watch(target_tree)


watch(target_tree)

# %%
# TODO: make functional, make pythonic, return actual target!
