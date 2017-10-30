#!/usr/bin/env python

import os
import requests

SRC_NAME = 'openoffice-scfuncs.src'
GIT_HASHES = {
    'openoffice': 'c014b5f2b55cff8d4b0c952d5c16d62ecde09ca1',
}
SRC_URLS = {
    'openoffice-scfuncs.src': 'https://github.com/apache/openoffice/raw/%s/main/sc/source/ui/src/scfuncs.src' %
                              GIT_HASHES['openoffice'],
}

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPTS_DIR, '_cache')

def get_src():
    url = SRC_URLS[SRC_NAME]
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError("Got unexpected response %s (%s)" % (r.reason, r.status_code))
    return r.content

if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    src = get_src()
    with open(os.path.join(CACHE_DIR, SRC_NAME), 'wb') as f:
        f.write(src)
