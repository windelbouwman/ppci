#!/usr/bin/env python3
"""
Atalla ISA Disassembler
Decodes 48-bit Atalla instructions from ELF binary
"""

def extract_bits(value, start, end):
    """Extract bits [start:end) from value (LSB = bit 0)"""
    mask = (1 << (end - start)) - 1
    return (value >> start) & mask

def bytes_to_int40(data):
    """Convert 5 bytes to 40-bit integer (little-endian)"""
    return int.from_bytes(data, byteorder='little')

def sign_extend(value, bits):
    """Sign extend a value from 'bits' width to full int"""
    sign_bit = 1 << (bits - 1)
    if value & sign_bit:
        return value - (1 << bits)
    return value

# Opcode mappings (from ISA spec)
OPCODES = {
    # R-type
    0b0000001: ("add_s", "R"),
    0b0000010: ("sub_s", "R"),
    0b0000011: ("mul_s", "R"),
    0b0000100: ("div_s", "R"),
    0b0000101: ("mod_s", "R"),
    0b0000110: ("or_s", "R"),
    0b0000111: ("and_s", "R"),
    0b0001000: ("xor_s", "R"),
    0b0001001: ("sll_s", "R"),
    0b0001010: ("srl_s", "R"),
    0b0001011: ("sra_s", "R"),
    0b0001100: ("slt_s", "R"),
    0b0001101: ("sltu_s", "R"),
    
    # BF16 operations (R-type format, different opcodes) #these are not in instructions.py yet
    0b0001110: ("add.bf", "R"),
    0b0001111: ("sub.bf", "R"),
    0b0010000: ("mul.bf", "R"),
    0b0010001: ("div.bf", "R"),
    0b0010010: ("slt.bf", "R"),
    0b0010011: ("sltu.bf", "R"),
    0b0010100: ("stbf_s", "I"),
    0b0010101: ("bfts_s", "I"),
    
    # I-type
    0b0010110: ("addi_s", "I"),
    0b0010111: ("subi_s", "I"),
    0b0011000: ("muli_s", "I"),
    0b0011001: ("divi_s", "I"),
    0b0011010: ("modi_s", "I"),
    0b0011011: ("ori_s", "I"),
    0b0011100: ("andi_s", "I"),
    0b0011101: ("xori_s", "I"),
    0b0011110: ("slli_s", "I"),
    0b0011111: ("srli_s", "I"),
    0b0100000: ("srai_s", "I"),
    0b0100001: ("slti_s", "I"),
    0b0100010: ("sltui_s", "I"),
    
    # BR-type
    0b0100011: ("beq_s", "BR"),
    0b0100100: ("bne_s", "BR"),
    0b0100101: ("blt_s", "BR"),
    0b0100110: ("bge_s", "BR"),
    0b0100111: ("bgt_s", "BR"),
    0b0101000: ("ble_s", "BR"),
    
    # M-type
    0b0101001: ("lw_s", "M"),
    0b0101010: ("sw_s", "M"),
    
    # MI-type
    0b0101011: ("jal", "MI"),
    0b0101100: ("jalr", "I"),
    0b0101101: ("li_s", "MI"),
    0b0101110: ("lui_s", "MI"),
    
    # S-type
    0b0101111: ("nop", "S"),
    0b0110000: ("halt", "S"),
    0b0110001: ("barrier", "S"),
    
    # Vector operations - I don't think these are in instructions.py yet either
    0b0110010: ("add.vv", "VV"),
    0b0110011: ("sub.vv", "VV"),
    
    # nop prolly
    0b0000000: ("nop", "S"),
    # halt prolly
    0b1111111: ("halt", "S"),
}

def disassemble_instruction(insn_int, offset):
    """Disassemble a 40-bit Atalla instruction"""
    
    # Extract opcode (bits 0-6)
    opcode = extract_bits(insn_int, 0, 7)
    
    if opcode not in OPCODES:
        return f"UNKNOWN (opcode=0x{opcode:02X})"
    
    mnemonic, fmt = OPCODES[opcode]
    
    if fmt == "R":
        # R-type: opcode rd rs1 rs2 reserved
        rd = extract_bits(insn_int, 7, 15)
        rs1 = extract_bits(insn_int, 15, 23)
        rs2 = extract_bits(insn_int, 23, 31)
        return f"{mnemonic:10s} x{rd}, x{rs1}, x{rs2}"
    
    elif fmt == "I":
        # I-type: opcode rd rs1 imm12 reserved
        rd = extract_bits(insn_int, 7, 15)
        rs1 = extract_bits(insn_int, 15, 23)
        imm12 = extract_bits(insn_int, 23, 35)
        imm12_signed = sign_extend(imm12, 12)
        return f"{mnemonic:10s} x{rd}, x{rs1}, {imm12_signed}"
    
    elif fmt == "BR":
        # BR-type: opcode incr_imm7 i1 rs1 rs2 imm9
        print("BR")
        incr_imm7 = extract_bits(insn_int, 7, 14)
        i1 = extract_bits(insn_int, 14, 15)
        rs1 = extract_bits(insn_int, 15, 23)
        rs2 = extract_bits(insn_int, 23, 31)
        imm9 = extract_bits(insn_int, 31, 40)
        
        # Reconstruct imm10 = {imm9, i1}
        imm10 = (imm9 << 1) | i1
        imm10_signed = sign_extend(imm10, 10)
        
        # PC-relative offset (multiply by 5 for byte offset)
        byte_offset = imm10_signed * 6
        target = offset + byte_offset
        
        return f"{mnemonic:10s} x{rs1}, x{rs2}, 0x{target:X}  # offset={imm10_signed}"
    
    elif fmt == "M":
        # M-type: opcode rd rs1 imm12 reserved
        rd = extract_bits(insn_int, 7, 15)
        rs1 = extract_bits(insn_int, 15, 23)
        imm12 = extract_bits(insn_int, 23, 35)
        imm12_signed = sign_extend(imm12, 12)
        return f"{mnemonic:10s} x{rd}, {imm12_signed}(x{rs1})"
    
    elif fmt == "MI":
        # MI-type: opcode rd imm25
        rd = extract_bits(insn_int, 7, 15)
        imm25 = extract_bits(insn_int, 15, 40)
        # print("MI")
        
        if mnemonic == "jal":
            # PC-relative jump
            imm25_signed = sign_extend(imm25, 25)
            byte_offset = imm25_signed * 6
            target = offset + byte_offset
            return f"{mnemonic:10s} x{rd}, 0x{target:X}  # offset={imm25_signed}"
        else:
            # Load immediate
            return f"{mnemonic:10s} x{rd}, {imm25}"
    
    elif fmt == "S":
        # S-type: just opcode
        return f"{mnemonic:10s}"
    
    return f"UNIMPLEMENTED FORMAT: {fmt}"

# In disassemble.py, replace hardcoded bounds with:
def get_code_section_bounds(elf_path):
    """Extract code section start and size from ELF"""
    with open(elf_path, 'rb') as f:
        data = f.read()
    
    shoff = int.from_bytes(data[0x20:0x24], 'little')
    shentsize = int.from_bytes(data[0x2E:0x30], 'little')
    shnum = int.from_bytes(data[0x30:0x32], 'little')
    shstrndx = int.from_bytes(data[0x32:0x34], 'little')
    
    strtab_header_off = shoff + shstrndx * shentsize
    strtab_header = data[strtab_header_off : strtab_header_off + shentsize]
    strtab_offset = int.from_bytes(strtab_header[16:20], 'little')
    
    for i in range(shnum):
        sh_offset = shoff + i * shentsize
        sh = data[sh_offset : sh_offset + shentsize]
        
        name_offset = int.from_bytes(sh[0:4], 'little')
        name_start = strtab_offset + name_offset
        name_end = data.index(b'\x00', name_start)
        section_name = data[name_start:name_end].decode('ascii')
        
        if section_name == "code":
            code_offset = int.from_bytes(sh[16:20], 'little')
            code_size = int.from_bytes(sh[20:24], 'little')
            return code_offset, code_offset + code_size
    
    return 0x34, 0xF0  # Fallback

def disassemble_elf(input_file, output_file):
    """Disassemble Atalla code from ELF file"""
    
    with open(input_file, 'rb') as f:
        data = f.read()
    
    with open(output_file, 'w') as out:
        out.write(f"Atalla Disassembly: {input_file}\n")
        out.write("=" * 100 + "\n\n")
        
        # Code section starts around 0x30, ends around 0xF0
        # code_start = 0x34  # Adjust if needed
        # code_end = 0xF0
        # Then use it:
        code_start, code_end = get_code_section_bounds(input_file)
        
        out.write("=== CODE SECTION ===\n\n")
        out.write(f"{'Offset':<10} {'Bytes':<30} {'Instruction'}\n")
        out.write("-" * 100 + "\n")
        
        offset = code_start
        while offset < code_end:
            if offset + 6 <= len(data):
                # Read 5 bytes (40 bits)
                insn_bytes = data[offset:offset+6]
                insn_int = bytes_to_int40(insn_bytes)
                
                # Format bytes
                hex_str = ' '.join(f'{b:02X}' for b in insn_bytes)
                
                # Disassemble
                disasm = disassemble_instruction(insn_int, offset)
                
                out.write(f"0x{offset:04X}    {hex_str:<28} {disasm}\n")
                
                offset += 6
            else:
                break
        
        out.write("\n" + "=" * 100 + "\n")

if __name__ == "__main__":
    disassemble_elf("output.elf", "disassembly.txt")
    print("Disassembly written to disassembly.txt")
