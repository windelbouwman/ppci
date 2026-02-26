extern int helper(int);

int helper2(int a, int b) {
    int c = a / b;
    return c;
}

int instruct_tests(int a, int b) {
    int r = a + b;

    int h = helper(r);

    int q = helper(h);

    q = helper2(q, h);

    return h + 5;
}

int main() {
    int a = 2;
    int b = 3;
    instruct_tests(a, b);
    return 0;
}
