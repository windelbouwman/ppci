import re 
import io
from ppci.lang.tools.lr import LrParserBuilder
from ppci.common import make_num
from ppci.lang.tools.grammar import Grammar
from ppci.lang.tools.baselex import BaseLexer, EPS, EOF 

datasection = False
code2sig = {}
data = {}
timemul = 1

def timeunit2val(timeval):
    unit2exp = {
    'f' : 1e-15,
    'p' : 1e-12,
    'n' : 1e-09,
    'u' : 1e-06,
    'm' : 1e-03,
    } 
    return unit2exp[timeval[-2]]

class VcdLexer(BaseLexer):
    """ Lexer capable of lexing a single line """
    kws = ['COMMENT','$SCOPE','$UPSCOPE','MODULE','TASK','BEGIN','$TIMESCALE',
    'UPSCOPE','$VAR','WIRE','REG','TRIREG','INTEGER','$END'] 
    
    def __init__(self):
        tok_spec = [
           ('HEXNUMBER', r'0x[\da-fA-F]+', self.handle_number),
           ('TIMEUNIT', r'\d+[unp]s', self.handle_timeunit), 
           ('NUMBER', r'\d+ ', self.handle_number), 
           ('ID', r'[^ ]+', self.handle_id), 
           ('SKIP', r'[ \t\r\n]', None)
            ]
        super().__init__(tok_spec) 

    def handle_id(self, typ, val):
        vu = val.upper()
        if vu in self.kws:
            typ = vu
        return typ, vu

    def handle_number(self, typ, val):
        """ Handle a number during lexing """
        val = make_num(val)
        typ = 'NUMBER'
        return typ, val
    
    def handle_timeunit(self, typ, val):
        """ Handle timeunit during lexing """
        #val = make_num(val[:-2])*timeunit2val(val)
        val = timeunit2val(val)
        typ = 'TIMEUNIT'
        return typ, val
    
    def tokenize(self, txt):
        global datasection
        global timemul
        lines = txt.split('\n')
        liter = iter(lines)
        for line in liter:
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            elif '$date' in line or '$version' in line:
                while '$end' not in line:
                    line = next(liter)
            elif '$enddefinitions' in line:
                datasection = True
            elif datasection:
                if line[0] in ('b', 'B', 'r', 'R'):
                    (value,code) = line[1:].split() 
                    if (code in data):
                        if 'tv' not in data[code]:
                            data[code]['tv'] = []
                        data[code]['tv'].append( (self.time, value) ) 
                elif line[0] in ('0', '1', 'x', 'X', 'z', 'Z'):
                    value = line[0]
                    code = line[1:]
                    if (code in data):
                        if 'tv' not in data[code]:
                            data[code]['tv'] = []
                        data[code]['tv'].append( (self.time, value) )
                elif line.startswith('#'):
                    self.time = timemul*make_num(line[1:])
            else:
                for tk in super().tokenize(line):
                    yield tk 

class VcdParser:
    def __init__(self, kws, sigfilter, opt_timescale):
        toks = ['ID', 'NUMBER', 'STRING','TIMEUNIT', EPS, EOF] + kws
        g = Grammar()
        g.add_terminals(toks)
        g.add_production('input', ['exp_list']) 
        g.add_one_or_more('exp', 'exp_list') 
        g.add_production('exp', ['$SCOPE', 'scopetype', 'ID', '$END'], 
        self.handle_start_module)
        g.add_production('scopetype', ['MODULE'],lambda l:l)
        g.add_production('scopetype', ['TASK'],lambda l:l)
        g.add_production('scopetype', ['BEGIN'],lambda l:l)
        g.add_production('exp', ['$UPSCOPE', '$END'], 
        self.handle_end_module)
        g.add_production('exp', ['$TIMESCALE', 'TIMEUNIT', '$END'], 
        self.handle_timescale)
        g.add_production('exp', ['$VAR', 'type', 'NUMBER', 'code', 'name', '$END'], 
        self.handle_vardecl)
        g.add_production('code', ['ID'],lambda l:l)
        g.add_production('code', ['NUMBER'],self.handle_number)
        g.add_production('name', ['ID'],lambda l:l)
        g.add_production('name', ['ID','ID'], self.handle_index)
        g.add_production('type', ['WIRE'],lambda l:l)
        g.add_production('type', ['REG'],lambda l:l)
        g.add_production('type', ['INTEGER'],lambda l:l)
        g.add_production('type', ['TRIREG'],lambda l:l)
        g.start_symbol = 'input'
        self.p = LrParserBuilder(g).generate_parser()
        self.sigprefix = []
        self.sigfilter = sigfilter
        self.timescale = opt_timescale

    def parse(self, lexer):
        self.p.parse(lexer)
    
    def handle_index(self, name, index):
        name.val += index.val
        return(name)
    
    def handle_number(self, num):
        num.val = str(num.val)
        return(num)
  
    def handle_start_module(self, scope_tag, module_tag, name, end_tag):
        self.sigprefix.append(name.val)
        
    def handle_end_module(self, scope_tag, end_tag):
        name = self.sigprefix.pop()

    def handle_timescale(self, time_tag, timeunit, end_tag):
        global timemul
        timemul = timeunit.val / timeunit2val(self.timescale)
    
    def handle_vardecl(self, var_tag, typeinfo, width, key, signame, end_tag):
        global data, code2sig
        path = '.'.join(self.sigprefix)
        name = path + '.' + signame.val
        if name in self.sigfilter:
            if key.val not in data:
                data[key.val] = {} 
            if 'nets' not in data[key.val]:
                data[key.val]['nets'] = []
            sig_data = {
                        'type' : typeinfo.val,
                        'name' : signame.val,
                        'size' : width.val,
                        'hier' : path,
                    }  
            data[key.val]['nets'].append(sig_data) 
            code2sig[name] = key.val
            


    
def parse_vcd(file, siglist = [], opt_timescale='ns'):
    global data
    with open(file, "r") as f: 
        lexer = VcdLexer()
        parser = VcdParser(lexer.kws, sigfilter = siglist, opt_timescale = opt_timescale)
        lexer.feed(f.read()) 
        parser.parse(lexer)
    return(data)
    

if __name__ == '__main__': 
    res = parse_vcd('picorv32.vcd',['TOP.V.PICORV32_CORE.DBG_REG_X10[31:0]'],'us')
    