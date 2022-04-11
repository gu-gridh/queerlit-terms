from configparser import ConfigParser
from os import listdir
from shutil import which
from subprocess import run

version = '0.2'

SCHEMA_TTL = f"""
<https://queerlit.dh.gu.se/qlit/{version}> a skos:ConceptScheme;
   skos:prefLabel "Queerlit"@sv;
   skos:hasTopConcept <https://queerlit.dh.gu.se/qlit/{version}/könsidentitet>;
   skos:hasTopConcept <https://queerlit.dh.gu.se/qlit/{version}/HBTQIPersoner> .
"""

config = ConfigParser()
config.read('config.ini')

files = [f for f in listdir(config['ttl']['ttls_dir']) if f.endswith('.ttl')]
files.sort()
prefix_lines = []
other_lines = []
validate = which('ttl') is not None
for file in files:
    file_path = config['ttl']['ttls_dir'] + file

    if validate:
        try:
            validate_result = run(['ttl', file_path],
                                  check=True, capture_output=True, start_new_session=True)
        except KeyboardInterrupt:
            exit
        except:
            print('Skipping invalid file', file)
            continue

    other_lines.append('\n')
    with open(file_path) as fp:
        for line in fp.readlines():
            if line.startswith('@prefix'):
                if line not in prefix_lines:
                    prefix_lines.append(line)
            elif line != '\n':
                line = line.replace('http://queerlit.se/qlit',
                                    'https://queerlit.dh.gu.se/qlit/' + version)
                line = line.replace('http://queerlit.se/termer',
                                    'https://queerlit.dh.gu.se/qlit/' + version)
                other_lines.append(line)

with open('qlit.ttl', 'w') as fp:
    fp.writelines(prefix_lines)
    fp.write(SCHEMA_TTL + '\n')
    fp.writelines(other_lines)
