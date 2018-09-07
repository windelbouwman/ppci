
"""
Load an ELF file and create a detailed report about its statistics.
"""

import argparse
from ppci.format.elf import read_elf
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument('elf_file')
args = parser.parse_args()
elf_filename = args.elf_file

with open(elf_filename, 'rb') as f:
    x = read_elf(f)

data = [(s.name, len(s.data)) for s in x.sections]

data.sort(key=lambda s: s[1])
section_sizes = [s[1] for s in data]
labels = [s[0] for s in data]

fig1, ax1 = plt.subplots()
ax1.pie(section_sizes, labels=labels, autopct='%1.1f%%')
ax1.axis('equal')

plt.show()
