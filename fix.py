import os
import re
from unicodedata import normalize

PATH_CURRENT = '/Users/arildm/University of Gothenburg/Olov Kriström - TTLs/'


def fn_to_term(fn):
    m = re.match(r'^- (.*).ttl$', fn)
    return normalize('NFC', m.group(1)) if m else None


terms = [fn_to_term(fn) for fn in os.listdir(PATH_CURRENT) if fn_to_term(fn)]


def remove_broken_links(fn):
    new_content = ''
    with open(os.path.join(PATH_CURRENT, fn)) as f:
        for line in f.readlines():
            m = re.search(r'<http[^>]+/qlit/([^>]+)>', line)
            if m:
                term = m.group(1)
                exit
                if term not in terms:
                    if term.lower() in [term.lower() for term in terms]:
                        print('--- Wrong case in: ', fn)
                        print(line)
                    else:
                        print('--- Skipping broken link in: ', fn)
                        print(line)
                        continue
            new_content += line
    return new_content


def remove_broken_links_all(inplace=False):
    for fn in os.listdir(PATH_CURRENT):
        if fn.endswith('.ttl'):
            os.makedirs('out', exist_ok=True)
            with open('out/' + fn, 'w') as f:
                f.write(remove_broken_links(fn))
