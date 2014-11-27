
# Plot the lines of file over time

import os
import subprocess
import re


def calc_diff(patch):
    add = 0
    sub = 0
    py_file = False
    for r in patch.split('\n'):
        if r.startswith('---'):
            py_file = '.py' in r
        elif r.startswith('+++'):
            py_file = py_file or ('.py' in r)
        elif py_file:
            if r.startswith('+'):
                add += 1
            elif r.startswith('-'):
                sub += 1
    return add, sub


def changed_lines_in_changeset(rev):
    res = subprocess.check_output(['hg', 'diff', '-c', str(rev)])
    res = res.decode('ascii')
    return calc_diff(res)


def lines_since_0(rev):
    res = subprocess.check_output(['hg', 'diff', '-r', '0', '-r', str(rev)])
    res = res.decode('ascii', errors='ignore')
    return calc_diff(res)

changed_lines_in_changeset(0)

res = subprocess.check_output(['hg', 'id', '-n'])
print(res)
rev = int(res[:-2])


count = 0
rev_map = {}
for i in range(rev+1):
    if i == 0:
        add0, sub0 = changed_lines_in_changeset(0)
        add = add0
        sub = sub0
    else:
        add, sub = lines_since_0(i)
        add += add0
        sub += sub0
    count = count + add - sub
    print(i, rev, add, sub, count)
    rev_map[i] = (add, sub)
