#!/usr/bin/env python

import os
import requests
import re

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

BLOCK_COMMENT = re.compile('/[*].*[*]/', re.DOTALL)
RESOURCE_START = re.compile('^\tResource ([A-Z0-9_]*)\n\t{', re.MULTILINE)
RESOURCE_END = re.compile('^\t};', re.MULTILINE)
STRING_START = re.compile('^\t\tString ([0-9]*) // (.*)\n\t\t{', re.MULTILINE)
STRING_END = re.compile('^\t\t};', re.MULTILINE)
TEXT_STR = re.compile(r'^\s*Text\s*\[\s*([a-zA-Z0-9_-]*)\s*\]\s*=\s*"([^"]*)"\s*;', re.MULTILINE)

def parse_src(src):
    src = BLOCK_COMMENT.sub('', src)
    src = src.replace('Resource RID_SC_FUNCTION_DESCRIPTIONS1\n{', '')
    src = src.replace('};\n\nResource RID_SC_FUNCTION_DESCRIPTIONS2\n{', '')
    src = src.replace('#if defined(U2S)\n#undef U2S\n#endif', '')
    src = src.rstrip()
    if src.endswith('};'):
        src = src[:src.rfind('};')].rstrip()
    for resource_start in RESOURCE_START.finditer(src):
        resource_name = resource_start.group(1)
        resource_end = RESOURCE_END.search(src, resource_start.start())
        if not resource_end:
            continue
        resource_str = src[resource_start.end():resource_end.start()]
        for string_start in STRING_START.finditer(resource_str):
            string_name = string_start.group(1)
            string_description = string_start.group(2)
            string_end = STRING_END.search(resource_str, string_start.start())
            if not string_end:
                continue
            string_src = resource_str[string_start.end():string_end.start()]
            for text_str in TEXT_STR.finditer(string_src):
                text_lang = text_str.group(1)
                text = text_str.group(2)
                # print(resource_name, string_name, string_description, text)


if __name__ == '__main__':
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    src_file = os.path.join(CACHE_DIR, SRC_NAME)
    if os.path.exists(src_file):
        with open(src_file, 'rb') as f:
            src = f.read()
    else:
        src = get_src()
        with open(os.path.join(CACHE_DIR, SRC_NAME), 'wb') as f:
            f.write(src)
    parse_src(src)
