from os import listdir
from os.path import dirname, realpath

dir_path = dirname(realpath(__file__))
files = [f for f in listdir(dir_path) if f.endswith('.ttl') and f != 'qlit.ttl']
files.sort()
prefix_lines = []
other_lines = []
for file in files:
    other_lines.append('\n')
    with open(file) as fp:
        for line in fp.readlines():
            if line.startswith('@prefix'):
                if line not in prefix_lines:
                    prefix_lines.append(line)
            elif line != '\n':
                line = line.replace('http://queerlit.se/qlit', 'https://queerlit.dh.gu.se/qlit/0.1')
                line = line.replace('http://queerlit.se/termer', 'https://queerlit.dh.gu.se/qlit/0.1')
                other_lines.append(line)

with open('qlit.ttl', 'w') as fp:
    fp.writelines(prefix_lines + other_lines)
