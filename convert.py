from os import listdir

version = '0.2'

SCHEMA_TTL = f"""
<https://queerlit.dh.gu.se/qlit/{version}> a skos:ConceptScheme;
   skos:prefLabel "Queerlit"@sv;
   skos:hasTopConcept <https://queerlit.dh.gu.se/qlit/{version}/könsidentitet>;
   skos:hasTopConcept <https://queerlit.dh.gu.se/qlit/{version}/HBTQIPersoner> .
"""

dir_path = '/Users/arildm/University of Gothenburg/Olov Kriström - TTLs/'
files = [f for f in listdir(dir_path) if f.endswith('.ttl')]
files.sort()
prefix_lines = []
other_lines = []
for file in files:
    file_path = dir_path + file
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
