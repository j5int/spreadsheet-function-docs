#!/usr/bin/env python

"""This is a utility that downloads source code and produces a JSON file with the documentation for spreadsheet functions from that source code"""

# The copyright holders licenses this file to you under the Apache License, Version 2.0 (the \"License\");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in this directory at LICENSE.md or at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an \"AS IS\" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.

import json
import logging
import os
import requests
import re

SRC_NAME = 'openoffice'

TARGET_FILE = '%s-function-docs.json' % SRC_NAME

SRC_FILES = {
    'openoffice': ['scfuncs.src', 'core_resource.src'],
}

GIT_HASHES = {
    'openoffice': 'trunk',
}

RAW_PREFIX = {
    'openoffice': 'https://github.com/apache/openoffice/raw/%s/' % GIT_HASHES['openoffice'],
}

SRC_URLS = {
    'openoffice': {
        'scfuncs.src': RAW_PREFIX['openoffice'] + 'main/sc/source/ui/src/scfuncs.src',
        'core_resource.src': RAW_PREFIX['openoffice'] + 'main/formula/source/core/resource/core_resource.src',
    },
}


SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPTS_DIR, '_cache')

def get_package_info():
    """Returns the information about this package stored in package.json"""
    with open(os.path.join(SCRIPTS_DIR, 'package.json'), 'rb') as f:
        return json.load(f)

def download_src_files():
    """Downloads defined source files if they're not already downloaded"""
    files = {}
    logging.info("Obtaining %s files", SRC_NAME)
    for filename in SRC_FILES[SRC_NAME]:
        local_filename = os.path.join(CACHE_DIR, '%s-%s' % (SRC_NAME, filename))
        if os.path.exists(local_filename):
            logging.info("Reading %s", filename)
            with open(local_filename, 'rb') as f:
                files[filename] = f.read()
        else:
            url = SRC_URLS[SRC_NAME][filename]
            logging.info("Downloading %s from %s", filename, url)
            r = requests.get(url)
            if r.status_code != 200:
                raise ValueError("Got unexpected response %s (%s)" % (r.reason, r.status_code))
            files[filename] = src = r.content
            with open(local_filename, 'wb') as f:
                f.write(src)
    return files

BLOCK_COMMENT_START = re.compile('/[*]')
BLOCK_COMMENT_END = re.compile('[*]/')


def parse_src_files(src_files):
    """Parses all source files defined"""
    parsed = {}
    parsed['scfuncs'] = parse_scfuncs(src_files['scfuncs.src'])
    parsed['core_resource'] = parse_core_resource(src_files['core_resource.src'])
    return parsed


def parse_core_resource(src):
    """Parses OpenOffice core_resource.src"""
    RESOURCE_START = re.compile('^Resource ([A-Z0-9_]*)\n{', re.MULTILINE)
    RESOURCE_END = re.compile('^};', re.MULTILINE)
    TEXT_STR = re.compile(r'^\s*String\s+([A-Z0-9_]+)\s*{\s*Text\s*(\[\s*([a-zA-Z0-9_-]*)\s*\])?\s*=\s*"([^"]*)"\s*;\s*};', re.MULTILINE)
    resources = {}
    for resource_start in RESOURCE_START.finditer(src):
        resource_name = resource_start.group(1)
        resources[resource_name] = resource = []
        resource_end = RESOURCE_END.search(src, resource_start.start())
        if not resource_end:
            continue
        resource_str = src[resource_start.end():resource_end.start()]
        for text_str in TEXT_STR.finditer(resource_str):
            string_name = text_str.group(1)
            text_lang = text_str.group(3)
            text = text_str.group(4)
            resource.append((resource_name, string_name, text_lang, text))
    return resources


def parse_scfuncs(src):
    """Parses OpenOffice scfuncs.src"""
    _I = {'i1': '(?:\t|    )', 'i2': '(?:\t\t|        )'} # for handling indents
    RESOURCE_START = re.compile('^%(i1)sResource ([A-Z0-9_]*)\n%(i1)s{' % _I, re.MULTILINE)
    RESOURCE_END = re.compile('^%(i1)s};' % _I, re.MULTILINE)
    STRING_START = re.compile('^%(i2)sString ([0-9]*) // (.*)\n%(i2)s{' % _I, re.MULTILINE)
    STRING_END = re.compile('^%(i2)s};' % _I, re.MULTILINE)
    TEXT_STR = re.compile(r'^\s*Text\s*\[\s*([a-zA-Z0-9_-]*)\s*\]\s*=\s*"([^"]*)"\s*;', re.MULTILINE)
    # remove blocks that we don't need
    result = {}
    block_comments = []
    for block_comment_start in BLOCK_COMMENT_START.finditer(src):
        block_comment_end = BLOCK_COMMENT_END.search(src, block_comment_start.start())
        block_comment_text = src[block_comment_start.start():block_comment_end.end()]
        block_comments.append(block_comment_text)
    for block_comment in block_comments:
        if "License" in block_comment:
           result['license'] = block_comment.strip().strip('/').strip('*').replace('\n * ', '\n').replace('\n', ' ').strip()
        src = src.replace(block_comment, '')
    src = src.replace('Resource RID_SC_FUNCTION_DESCRIPTIONS1\n{', '')
    src = src.replace('};\n\nResource RID_SC_FUNCTION_DESCRIPTIONS2\n{', '')
    src = src.replace('#if defined(U2S)\n#undef U2S\n#endif', '')
    src = src.rstrip()
    if src.endswith('};'):
        src = src[:src.rfind('};')].rstrip()
    result['resources'] = resources = {}
    for resource_start in RESOURCE_START.finditer(src):
        resource_name = resource_start.group(1)
        resources[resource_name] = resource = []
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
                resource.append((resource_name, string_name, string_description, text_lang, text))
    return result


def generate_function_reference(parsed):
    """Takes the parsed contents of the source files and returns a function reference structure"""
    PARAMETER_DESC = re.compile('(.*) of Parameter ([0-9]*)')
    core_parsed = parsed['core_resource']
    name_lookup = {}
    for _, string_const, _, func_name in core_parsed['RID_STRLIST_FUNCTION_NAMES_ENGLISH_ODFF']:
        name_lookup[string_const] = func_name
    scfuncs_parsed = parsed['scfuncs']
    function_defs = {}
    for resource_id, resource_def in sorted(scfuncs_parsed['resources'].items()):
        func_name = name_lookup.get(resource_id, None)
        if not func_name:
            continue
        function_defs[func_name] = function_def = {}
        param_lookup = {}
        for _, _, string_description, _, text in resource_def:
            param_info = PARAMETER_DESC.match(string_description)
            if param_info:
                param_number = int(param_info.group(2))
                string_description = param_info.group(1)
                param_lookup.setdefault(param_number-1, {})[string_description] = text
            else:
                function_def[string_description] = text
        num_params = max([-1] + param_lookup.keys())
        function_def['Parameters'] = [param_lookup.get(param_number, {}) for param_number in range(0, num_params+1)]
    version = get_package_info()['version']
    return {'LICENSE': scfuncs_parsed['license'], 'VERSION': version, 'functions': function_defs}


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('requests').setLevel(logging.WARNING)
    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    src_files = download_src_files()
    parsed_files = parse_src_files(src_files)
    function_reference = generate_function_reference(parsed_files)
    target_filename = os.path.join(SCRIPTS_DIR, TARGET_FILE)
    logging.info("Saving function reference to %s", target_filename)
    with open(target_filename, 'wb') as f:
        json.dump(function_reference, f, indent=4, sort_keys=True)

