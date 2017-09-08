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

/* Pack importable funcs into a dict */

var providedfuncs = {
    print_ln: print_ln,
    print_charcode: print_charcode,
    alert: alert,
    perf_counter: perf_counter,
};


function compile_my_wasm() {
    print_ln('Compiling wasm module');
    var module_ = new WebAssembly.Module(wasm_data);
    print_ln('Initializing wasm module');
    print_ln('Result:');
    var module = new WebAssembly.Instance(module_, {js: providedfuncs});
    print_ln('\n');  // flush
    
}
