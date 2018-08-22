/* This code is used to run WASM modules in either Nodejs or the browser.
   In both cases, a couple of standard functions are provided, e.g. to
   print text.
*/


WASM_PLACEHOLDER

var is_node = typeof window === 'undefined';

/* Define functions to provide to the WASM module. */

function print_ln(x) {
    if (is_node) {
        process.stdout.write(x + '\n');
    } else {
        var el = document.getElementById('wasm_output');
        el.innerHTML += String(x).replace('\n', '<br>') + '<br>';
        console.log(x);
    }
}

function print_charcode(i) {
    var c = String.fromCharCode(i);
    if (is_node) {
        process.stdout.write(c);
    } else {
        if (c == '\n') { c = '<br>'; }
        var el = document.getElementById('wasm_output');
        el.innerHTML += c;
    }
}

function alert(x) {
    if (is_node) {
        process.stdout.write('ALERT: ' + x);
    } else {
        window.alert(x);
    }
}

function perf_counter() {
    if (is_node) {
        var t = process.hrtime();
        return t[0] + t[1] * 1e-9;
    } else {
        return performance.now() * 1e-3;
    }
}

function test_1_1() {
    print_ln('test_1_1 called');
}
function test_1_0() {
    print_ln('test_1_0 called');
}
function test_0_1() {
    print_ln('test_0_1 called');
    return 0;
}
function test_0_0() {
    print_ln('test_0_0 called');
}

/* Pack importable funcs into a dict */

/* old mechanics */
var providedfuncs = {
    print_ln: print_ln,
    print_charcode: print_charcode,
    bsp_putc: print_charcode,
    alert: alert,
    perf_counter: perf_counter,
    test_1_1: test_1_1,
    test_1_0: test_1_0,
    test_0_1: test_0_1,
    test_0_0: test_0_0
};

/* Newer style */
var envfuncs = {
    f64_print: print_ln
};


function compile_my_wasm() {
    print_ln('Compiling wasm module');
    var module_ = new WebAssembly.Module(wasm_data);
    print_ln('Initializing wasm module');
    print_ln('Result:');
    var t0 = perf_counter();
    var module = new WebAssembly.Instance(module_, {js: providedfuncs, env: envfuncs});
    print_ln('(in ' + (perf_counter() - t0) + ' s)');  // flush
    MAIN_JS_PLACEHOLDER

    print_ln('\n');  // flush
    
}
