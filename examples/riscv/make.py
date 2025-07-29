from ppci import api

march = api.get_arch("riscv")

with open("boot0.asm", "r") as f:
    obj1 = api.asm(f, march)

with open("sifive_u.mmap", "r") as f:
    obj = api.link([obj1], layout=f)

print(obj)

with open("kernel.elf", "wb") as f:
    api.write_elf(obj, f)
