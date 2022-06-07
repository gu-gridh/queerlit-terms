import re
from strgen import StringGenerator


PATTERN = r'[a-z]{2}[0-9]{2}[a-z]{2}[0-9]{2}'

def generate_identifier(blacklist: list[str] = []):
    gen = StringGenerator(PATTERN)
    ids = (gen.render() for i in range(100))
    for id in ids:
        if id not in blacklist:
            return id
    raise IndexError('Randomizer retries exhausted')

def validate_identifier(identifier):
    return bool(re.match(PATTERN + '$', identifier))