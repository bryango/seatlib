#!/usr/bin/env python
# coding: utf-8

# In[2]:


import json
import urllib.request
import random
import time
import sys

def eprint(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    print(*args, **kwargs)


# In[3]:


target_tree = {
    '文科图书馆': {
        '一层': { 'C区': {} },
        # '二层': { 'C区': {} },
    },
}


# In[4]:


SEAT_LIB_TSINGHUA = 'https://seat.lib.tsinghua.edu.cn/api.php/v3areas'
SLEEP_INTERVAL = [10, 20]


# In[5]:


def select_matching(listdicts, key, value):
    return [ entry for entry in listdicts if entry[key] == value ]


# In[6]:


def adopt_areas(dataset, parents: list):
    for parent in parents:
        parent['children'] = select_matching(dataset, 'parentId', parent['id'])
        adopt_areas(dataset, parents=parent['children']) 


# In[7]:


def timestamp():
    now = time.localtime()
    eprint(now.tm_hour, now.tm_min, now.tm_sec, sep=':', end='\t')

timestamp()
eprint()


# In[10]:


def recursive_match(selectors: dict, areas: list, parent_name: str=''):
    global available
    for site in areas:

        matched_keys = [ key for key in selectors if key in site['name'] ]
        # eprint(selectors, matched_keys)
        if not any(matched_keys):
            continue
        
        site['name'] = ' '.join([ parent_name, site['name'].strip() ]).strip()
        site_info = { attr: site[attr] for attr in [
            'name',
            'TotalCount'
        ] }
        site_info['AvailableSpace'] = (
            site['TotalCount']
            - site['UnavailableSpace']
        )

        next_selectors = selectors[matched_keys[0]]
        if not next_selectors:
            timestamp()
            # eprint(site)
            eprint(site_info)
            
            available += site_info['AvailableSpace']
            if available:
                return site_info
                # fix returns, or use break
            
            continue

        next_areas = site['children']
        recursive_match(next_selectors, next_areas, site['name'])

def main():
    global available
    while True:
        available = 0
        with urllib.request.urlopen(SEAT_LIB_TSINGHUA) as datafile:
            dataset = json.load(datafile)['data']['list']['seatinfo']

        area_tree = select_matching(dataset, 'parentId', 0)
        adopt_areas(dataset, area_tree)

        areas = area_tree
        selectors = target_tree
        hit = recursive_match(selectors, areas)
        if available:
            return hit
        time.sleep(random.uniform(*SLEEP_INTERVAL))

print(main())


# In[ ]:


# TODO: make functional, make pythonic, return actual target!

