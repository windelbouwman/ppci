import io
from ppci.api import asm, c3c, link, objcopy
from ppci.utils.reporting import HtmlReportGenerator, AsmReportGenerator, complete_report

# report_generator = HtmlReportGenerator(open("report.html", 'w'))
report_generator = AsmReportGenerator(open("report.asm", 'w'))
with complete_report(report_generator) as reporter:
    o1 = asm("starterirq.asm", "riscv")
    o2 = c3c(["bsp.c3", "io.c3", "gdbstub.c3", "main.c3", "irq.c3"], [], "riscv", reporter=reporter, debug=False,
             opt_level=2)
    obj = link([o1, o2], "firmware.mmap", use_runtime=False, reporter=reporter, debug=True)

    of = open("firmware.tlf", "w")
    obj.save(of)
    of.close()
    objcopy(obj, "flash", "elf", "firmware.elf")
    objcopy(obj, "flash", "bin", "firmware.bin")

    with open("firmware.bin", "rb") as f:
        bindata = f.read()

    wsize = 32768

    assert len(bindata) < wsize * 4
    assert len(bindata) % 4 == 0

    f = open("firmware.hex", "w")
    for i in range(wsize):
        if i < len(bindata) // 4:
            w = bindata[4 * i: 4 * i + 4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]), file=f)
        else:
            print("00000000", file=f)
    f.close()
