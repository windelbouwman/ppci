
package add;

fun my_add(x: Int, y: Int): Int {
    return x + y + 1
}

fun my_func(x: Int): Float {
    val z = my_add(x, 6);
    return 3.14f * z;
}
