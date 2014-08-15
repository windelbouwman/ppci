
%tokens ':' ';' '(' ')' ',' string id number '%%' '%terminal' header

%%

burgdef: header '%%' directives '%%' rules { self.system.header_lines = $1.val };

directives:
          | directives directive;

directive: termdef;

termdef: '%terminal' termids;

termids:
       | termids termid;

termid: id { self.system.add_terminal($1.val) };

rules:
     | rules rule;

rule: id ':' tree cost string { self.system.add_rule($1.val, $3, $4, None, $5.val) };
rule: id ':' tree cost string string { self.system.add_rule($1.val, $3, $4, $5.val, $6.val) };

cost: number { return $1.val };

tree: id { return self.system.tree($1.val) }
    | id '(' tree ')' { return self.system.tree($1.val, $3) }
    | id '(' tree ',' tree ')' { return self.system.tree($1.val, $3, $5) };

