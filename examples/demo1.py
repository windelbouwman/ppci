
def a(x: int, y: int) -> int:
    t = x + y
    if x > 10:
        return t
    else:
        if t > 5:
            return x - y + 100
        else:
            c = 55 - x
    return c


def b(x: int) -> int:
    y = 100
    while x != 19:
        if y + x > 200:
            break
        x += 1
        for z in range(90):
            y += z
    return x / y
