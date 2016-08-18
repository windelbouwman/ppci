import io
from ppci.api import asm, c3c, link, objcopy
from ppci.utils.reporting import HtmlReportGenerator, complete_report

report_generator = HtmlReportGenerator(open("report.html", 'w'))
with complete_report(report_generator) as reporter:
    
    o1 = asm("startercode.asm", "riscv:rvc")
    o2 = c3c(["bsp.c3", "io.c3", "main.c3"], [], "riscv:rvc", reporter=reporter, debug=True, opt_level=2)
    obj = link([o1,o2], "firmware.mmap", use_runtime=False,reporter=reporter, debug=True)
    o1f = open("samples.txt","w")
    obj.save(o1f)
    o1f.close()
    objcopy(obj, "flash", "elf", "samples.elf")
    objcopy(obj, "flash", "bin", "flash.bin")
    objcopy(obj, "flash", "ldb", "debug.txt")
    objcopy(obj, "ram", "bin", "ram.bin")
    
    with open("flash.bin", "rb") as f:
        bindata = f.read()

    assert len(bindata) % 4 == 0

    f = open("l2_stim.slm","w")
    for i in range(0x8000//4):
        if i < len(bindata) // 4:
            w = bindata[4*i : 4*i+4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]),file=f)
    f.close()
    
    with open("ram.bin", "rb") as f:
        bindata = f.read()
    
    assert len(bindata) % 4 == 0

    f = open("tcdm_bank0.slm","w")
    for i in range(0x6000//4):
        if i < len(bindata) // 4:
            w = bindata[4*i : 4*i+4]
            print("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0]),file=f)
    f.close()
   
