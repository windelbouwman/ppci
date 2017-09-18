

from ppci import api
from ppci.utils.reporting import HtmlReportGenerator

arch = api.get_arch('mcs6500')
print('Using arch', arch)

with open('report.html', 'w') as f2, HtmlReportGenerator(f2) as reporter:
    with open('add.c') as f:
        oj = api.cc(f, arch, reporter=reporter)

print(oj)
