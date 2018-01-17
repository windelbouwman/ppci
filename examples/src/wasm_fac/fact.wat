(module
  (func $fac (param i32) (result i32)
    get_local 0
    i32.const 1
    i32.lt_s
    if (result i32)
      i32.const 1
    else
      get_local 0
      get_local 0
      i32.const 1
      i32.sub
      call $fac
      i32.mul
    end)
  (export "main_fac" (func $fac)))
