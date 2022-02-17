import os
import re
from unicodedata import normalize

PATH_CURRENT = '/Users/arildm/University of Gothenburg/Olov Kriström - TTLs/'
PATH_REMOVED = '/Users/arildm/University of Gothenburg/Olov Kriström - Strukna/'


def fn_to_term(fn):
    m = re.match(r'^\(?- ([^)]*)\)?.ttl$', fn)
    return normalize('NFC', m.group(1)) if m else None


terms = [fn_to_term(fn) for fn in os.listdir(PATH_CURRENT) if fn_to_term(fn)]
terms_removed = [fn_to_term(fn)
                 for fn in os.listdir(PATH_REMOVED) if fn_to_term(fn)]


def remove_broken_links(fn, quiet=False):
    new_content = ''
    with open(os.path.join(PATH_CURRENT, fn)) as f:
        for line in f.readlines():
            m = re.search(r'<http[^>]+/qlit/([^>]+)>', line)
            if m:
                term = m.group(1)
                # Remove a line containing a discarded term
                if term in terms_removed:
                    print('Ghost link', fn)
                    print(line)
                    continue
                # Warn about other things
                if not quiet:
                    if term not in terms:
                        if term.lower() in [term.lower() for term in terms]:
                            print('Warning: Wrong case', fn)
                            print(line)
                        else:
                            print('Warning: Missing link', fn)
                            print(line)
            new_content += line
    return new_content


def remove_broken_links_all(quiet=False, inplace=False):
    for fn in os.listdir(PATH_CURRENT):
        if fn.endswith('.ttl'):
            os.makedirs('out', exist_ok=True)
            with open('out/' + fn, 'w') as f:
                f.write(remove_broken_links(fn, quiet))


if __name__ == '__main__':
    remove_broken_links_all()
