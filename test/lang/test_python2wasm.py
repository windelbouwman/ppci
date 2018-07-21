"""
This tets the python_to_wasm compiler, and also touches on some wasm-specifics,
such as the floor operator.
"""

from ppci.lang.python import python_to_wasm
from ppci import wasm


def find_prime(nth):
    n = 0
    i = -1       
    while n < nth:
        i = i + 1        
        if i <= 1:
            continue  # nope
        elif i == 2:
            n = n + 1
        else:
            gotit = 1
            for j in range(2,  i//2+1):
                if i % j == 0:
                    gotit = 0
                    break
            if gotit == 1:
                n = n + 1    
    return i
    

def f64_print(x:float) -> None:
    print(x)


def test_python_to_wasm():
    
    m = python_to_wasm(find_prime)

    imports = {'env': {'f64_print': f64_print}}
    ob = wasm.instantiate(m, imports)
    
    result = ob.exports.find_prime(1000)
    assert result == 7919


if __name__ == '__main__':
    test_python_to_wasm()
