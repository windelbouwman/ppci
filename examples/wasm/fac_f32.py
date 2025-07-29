import io
from ppci.wasm import Module, instantiate
from ppci import api

src = """
(module

  (type $over-f32 (func (param f32) (result f32)))

  (func $fac-f32 (export "fac-f32") (type $over-f32)
    (if (result f32) (f32.eq (local.get 0) (f32.const 0.0))
      (then (f32.const 1.0))
      (else
        (f32.mul
          (local.get 0)

          (call $fac-f32
            (f32.sub (local.get 0) (f32.const 1.0))
          )
        )
      )
    )
  )
)
"""
m = Module(src)

obj = api.wasmcompile(src, "x86_64", opt_level=0)
api.objcopy(obj, None, "elf", "fac_f32.o")


print(m.to_string())

inst = instantiate(m, target="native")
inst2 = instantiate(m, target="python")

for number in [1.0, 5.0, 10.0]:
    print(
        "number",
        number,
        "fac",
        inst.exports["fac-f32"](number),
        "fac_python",
        inst2.exports["fac-f32"](number),
    )
