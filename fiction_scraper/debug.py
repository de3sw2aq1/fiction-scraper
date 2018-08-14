"""Various debug utilities

Most fucntions in this module should be valid filters if possible: they should
take one root element as a parameter. Debug info is written to stderr.
"""


from collections import Counter
from sys import stderr


def count_attributes(root):
    counter = Counter()
    for e in root.iter():
        counter.update(e.attrib.items())

    for (name, value), count in counter.most_common():
        print(f'{count:4d}: {name}={value}', file=stderr)
