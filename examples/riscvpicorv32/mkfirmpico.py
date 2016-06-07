import io
from ppci.api import asm, c3c, link, objcopy
from ppci.utils.reporting import HtmlReportGenerator, complete_report

report_generator = HtmlReportGenerator(open("report.html", 'w'))
with complete_report(report_generator) as reporter:
    
    o1 = asm ("startercode.asm", "riscv")
    o2 = c3c(["bsp.c3", "io.c3", "main.c3"], [], "riscv",reporter=reporter)
    obj = link([o1,o2], "firmware.mmap", use_runtime=False,reporter=reporter)
    objcopy(obj, "flash", "bin", "firmware.bin")
    
    with open("firmware.bin", "rb") as f:
        bindata = f.read()

    assert len(bindata) < 60*1024
    assert len(bindata) % 4 == 0

    f = open("firmware.hex","w")
    for i in range(64*1024//4):
        if i < len(bindata) // 4:
            w = bindata[4*i : 4*i+4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]),file=f)
        else:
            print("0",file=f)
    f.close()