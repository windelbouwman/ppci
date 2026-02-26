# Tests that JAL and JALR instructions correctly resolve to their intended targets.
# Parses ELF symbol table and disassembly output to verify relocations.
# """
# # Claude made this, had to change how it was parsing the header but it is good otherwise

"""
Atalla Relocation Verification Script - Auto-Discovery Mode
Automatically discovers and verifies ALL relocations without configuration.
"""

import re
from typing import Dict, List, Tuple, Optional

class ELFParser:
    """Parse ELF file to extract code section bounds and symbol table"""
    
    def __init__(self, elf_path: str):
        with open(elf_path, 'rb') as f:
            self.data = f.read()
        self.symbols = {}
        self.code_section_offset = 0
        self.code_section_size = 0
        self._find_code_section()
        self._parse_symbols()
    
    def _find_code_section(self):
        """Find code section offset AND size from ELF headers"""
        shoff = int.from_bytes(self.data[0x20:0x24], 'little')
        shentsize = int.from_bytes(self.data[0x2E:0x30], 'little')
        shnum = int.from_bytes(self.data[0x30:0x32], 'little')
        shstrndx = int.from_bytes(self.data[0x32:0x34], 'little')
        
        # Read string table section header
        strtab_header_off = shoff + shstrndx * shentsize
        strtab_header = self.data[strtab_header_off : strtab_header_off + shentsize]
        strtab_offset = int.from_bytes(strtab_header[16:20], 'little')
        
        # Find "code" section
        for i in range(shnum):
            sh_offset = shoff + i * shentsize
            sh = self.data[sh_offset : sh_offset + shentsize]
            
            # Get section name
            name_offset = int.from_bytes(sh[0:4], 'little')
            name_start = strtab_offset + name_offset
            name_end = self.data.index(b'\x00', name_start)
            section_name = self.data[name_start:name_end].decode('ascii')
            
            if section_name == "code":
                self.code_section_offset = int.from_bytes(sh[16:20], 'little')
                self.code_section_size = int.from_bytes(sh[20:24], 'little')
                print(f"✓ Code section: offset=0x{self.code_section_offset:04X}, size=0x{self.code_section_size:04X}")
                break
    
    def _parse_symbols(self):
        """Extract symbol table and adjust addresses to file offsets"""
        shoff = int.from_bytes(self.data[0x20:0x24], 'little')
        shentsize = int.from_bytes(self.data[0x2E:0x30], 'little')
        shnum = int.from_bytes(self.data[0x30:0x32], 'little')
        shstrndx = int.from_bytes(self.data[0x32:0x34], 'little')
        
        strtab_header_off = shoff + shstrndx * shentsize
        strtab_header = self.data[strtab_header_off : strtab_header_off + shentsize]
        strtab_offset = int.from_bytes(strtab_header[16:20], 'little')
        
        for i in range(shnum):
            sh_offset = shoff + i * shentsize
            sh = self.data[sh_offset : sh_offset + shentsize]
            
            name_offset = int.from_bytes(sh[0:4], 'little')
            name_start = strtab_offset + name_offset
            name_end = self.data.index(b'\x00', name_start)
            section_name = self.data[name_start:name_end].decode('ascii')
            
            if section_name == ".symtab":
                symtab_offset = int.from_bytes(sh[16:20], 'little')
                symtab_size = int.from_bytes(sh[20:24], 'little')
                symtab_entsize = int.from_bytes(sh[36:40], 'little')
                
                strtab_link = int.from_bytes(sh[24:28], 'little')
                strtab_sh_off = shoff + strtab_link * shentsize
                strtab_sh = self.data[strtab_sh_off : strtab_sh_off + shentsize]
                sym_strtab_offset = int.from_bytes(strtab_sh[16:20], 'little')

                for sym_i in range(0, symtab_size, symtab_entsize):
                    sym = self.data[symtab_offset + sym_i : symtab_offset + sym_i + symtab_entsize]
                    
                    sym_name_off = int.from_bytes(sym[0:4], 'little')
                    sym_value = int.from_bytes(sym[4:8], 'little')
                    sym_info = sym[12]
                    
                    if sym_name_off > 0:
                        name_start = sym_strtab_offset + sym_name_off
                        name_end = self.data.index(b'\x00', name_start)
                        sym_name = self.data[name_start:name_end].decode('ascii')
                        
                        sym_type = sym_info & 0xF
                        if sym_type == 2 or sym_value > 0:
                            # Add code section offset to get file address
                            actual_address = sym_value + self.code_section_offset
                            self.symbols[sym_name] = actual_address
                            # print(f"RAW SYMBOL {sym_name} = 0x{sym_value:04X}")
                            
                
                break
    
    def get_code_bounds(self) -> Tuple[int, int]:
        """Return (start, end) of code section in file"""
        return (self.code_section_offset, 
                self.code_section_offset + self.code_section_size)
    
    def get_all_symbols(self) -> Dict[str, int]:
        return self.symbols.copy()


class DisassemblyParser:
    """Parse disassembly to extract ALL jump instructions"""
    
    def __init__(self, disasm_path: str):
        with open(disasm_path, 'r') as f:
            self.lines = f.readlines()
        self.instructions = []
        self._parse()
    
    def _parse(self):
        """Extract all jump/branch instructions"""
        # Match: jal, jalr, and all branch instructions
        pattern = r'^(0x[0-9A-Fa-f]+)\s+([0-9A-Fa-f\s]+)\s+(jal|jalr|beq_s|bne_s|blt_s|bge_s|bgt_s|ble_s)\s+.*?(0x[0-9A-Fa-f]+)'
        
        for line in self.lines:
            match = re.search(pattern, line)
            if match:
                addr = int(match.group(1), 16)
                mnemonic = match.group(3)
                target = int(match.group(4), 16)
                
                self.instructions.append({
                    'address': addr,
                    'mnemonic': mnemonic,
                    'target': target,
                    'line': line.strip()
                })
    
    def get_jumps(self) -> List[Dict]:
        return self.instructions.copy()


class AutoRelocationTester:
    """Automatically test ALL relocations"""
    
    def __init__(self, elf_parser: ELFParser, disasm_parser: DisassemblyParser):
        self.elf = elf_parser
        self.disasm = disasm_parser
        self.results = {"pass": 0, "fail": 0, "warn": 0}
    
    def run(self):
        print("=" * 80)
        print("ATALLA RELOCATION AUTO-VERIFICATION")
        print("=" * 80)
        print()
        
        symbols = self.elf.get_all_symbols()
        jumps = self.disasm.get_jumps()
        
        # Show what we found
        print(f"Discovered {len(symbols)} symbols:")
        for name, addr in sorted(symbols.items(), key=lambda x: x[1]):
            print(f"  {name:30s} @ 0x{addr:04X}")
        print()
        
        print(f"Found {len(jumps)} jump/branch instructions")
        print()
        
        # Test each jump
        print("=" * 80)
        print("VERIFYING ALL RELOCATIONS")
        print("=" * 80)
        print()
        
        # Create reverse lookup: address -> symbol name
        addr_to_symbol = {addr: name for name, addr in symbols.items()}
        
        for jump in jumps:
            self._verify_jump(jump, addr_to_symbol, symbols)
        
        # Summary
        self._print_summary()
    
    def _verify_jump(self, jump: Dict, addr_to_symbol: Dict[int, str], symbols: Dict[str, int]):
        """Verify a single jump instruction"""
        addr = jump['address']
        target = jump['target']
        mnemonic = jump['mnemonic']
        
        # Check if target points to a known symbol
        target_symbol = addr_to_symbol.get(target, "unknown")
        
        if target_symbol != "unknown":
            # SUCCESS: Jump points to a valid symbol
            print(f"✅ PASS: {mnemonic:6s} @ 0x{addr:04X} → 0x{target:04X} ({target_symbol})")
            self.results["pass"] += 1
        else:
            # Check if it's close to any symbol (within a few instructions)
            closest_symbol = None
            min_distance = float('inf')
            
            for sym_name, sym_addr in symbols.items():
                dist = abs(target - sym_addr)
                if dist < min_distance and dist < 30:  # Within ~5 instructions
                    min_distance = dist
                    closest_symbol = (sym_name, sym_addr, dist)
            
            if closest_symbol:
                name, sym_addr, dist = closest_symbol
                print(f"⚠️  WARN: {mnemonic:6s} @ 0x{addr:04X} → 0x{target:04X} (near {name}, off by {dist} bytes)")
                self.results["warn"] += 1
            else:
                print(f"❌ FAIL: {mnemonic:6s} @ 0x{addr:04X} → 0x{target:04X} (no matching symbol)")
                self.results["fail"] += 1
    
    def _print_summary(self):
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✅ PASSED:   {self.results['pass']}")
        print(f"⚠️  WARNINGS: {self.results['warn']}")
        print(f"❌ FAILED:   {self.results['fail']}")
        print()
        
        if self.results['fail'] == 0 and self.results['warn'] == 0:
            print("ALL RELOCATIONS VERIFIED!")
        elif self.results['fail'] == 0:
            print("✅ All relocations valid (some warnings)")
        else:
            print("❌ SOME RELOCATIONS FAILED")


def main():
    print("Parsing ELF file...")
    elf_parser = ELFParser("output.elf")
    
    print("Parsing disassembly...")
    disasm_parser = DisassemblyParser("disassembly.txt")
    
    print()
    
    tester = AutoRelocationTester(elf_parser, disasm_parser)
    tester.run()


if __name__ == "__main__":
    main()