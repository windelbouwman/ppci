
program main;

    procedure ppci_write_int(value, base: integer);
    var
        buf : array[0..30] of char;
        i, j, quotient, remainder : integer;
    begin
        base := 10;
        i := 0;

        if value < 0 then
            quotient := -value
        else
            quotient := value;

        repeat
            remainder := quotient mod base;
            
            if remainder < 10 then
                buf[i] := chr(48 + remainder)
            else
                buf[i] := '?';

            i := i + 1;

            quotient := quotient div base;
        until quotient = 0;

        if value < 0 then
            buf[i] := '-'
        else
            i := i - 1;

        for j := i downto 0 do
            put(buf[j]);
    end;

begin
    ppci_write_int(1337, 10);
    put(' ');
    ppci_write_int(42, 10);
    put(' ');
    ppci_write_int(0, 10);
    put(' ');
    ppci_write_int(1, 10);
    put(' ');
    ppci_write_int(-1, 10);
    put(' ');
    ppci_write_int(-1337, 10);
    put(chr(10));
end.
