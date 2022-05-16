"""
Saves copies of all source files with randomized identifiers.
"""

import os
import re
import unicodedata
from dotenv import load_dotenv
from strgen import StringGenerator

load_dotenv()

if __name__ == '__main__':
    if 'INDIR' not in os.environ:
        raise EnvironmentError('Error: INDIR missing from env')

    fns = [fn for fn in os.listdir(os.environ['INDIR']) if not fn.startswith('.')]

    id_generator = StringGenerator(r'[a-z]{2}[0-9]{2}[a-z]{2}[0-9]{2}')
    new_ids = id_generator.render_set(len(fns))
    for fn, new_id in zip(fns, new_ids):
        old_id = re.sub(r'- (.*).ttl', r'\1', fn)
        # See https://stackoverflow.com/questions/26732985/utf-8-and-os-listdir
        old_id = unicodedata.normalize('NFC', old_id)

        try:
            with open(os.path.join(os.environ['INDIR'], fn)) as f:
                data = f.read()

            subs = [
                (f'qlit/{re.escape(old_id)}>', f'qlit/{new_id}>'),
                (f'dc:identifier "{re.escape(old_id)}"', f'skos:identifier "{new_id}"'),
            ]

            for pattern, repl in subs:
                data2 = re.sub(pattern, repl, data)
                if data == data2:
                    raise Exception('Pattern not found: ' + pattern)
                data = data2

            with open(os.path.join('out', 'randomids', fn), 'w') as f:
                f.write(data)

        except Exception as err:
            # Report error and skip this input file.
            print(f'{fn}: {err}')
