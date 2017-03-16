"""
Decode all the instructions!

Usually you just want to call decode_instruction on your bytestream,
it'll return an (Instruction, length) pair. Just advance your bytestream
by length, and you can do whatever you want with the instructions.
I recommend symbolically executing them! :)
"""
from enum import Enum, unique
from z3 import is_bv, BitVecVal


@unique
class Opcode(Enum):
    """
    Opcodes for instructions.
    """
    # Single-operand family
    RRC = 0
    SWPB = 1
    RRA = 2
    SXT = 3
    PUSH = 4
    CALL = 5
    RETI = 6
    # Jump family
    JNZ = 7
    JZ = 8
    JNC = 9
    JC = 10
    JN = 11
    JGE = 12
    JL = 13
    JMP = 14
    # Double-operand family
    MOV = 15
    ADD = 16
    ADDC = 17
    SUBC = 18
    SUB = 19
    CMP = 20
    DADD = 21
    BIT = 22
    BIC = 23
    BIS = 24
    XOR = 25
    AND = 26


@unique
class OperandWidth(Enum):
    """
    An Operand can be 1-byte or 1-word long. We encode that with one of these.
    """
    WORD = 0
    BYTE = 1


@unique
class AddressingMode(Enum):
    """
    Instructions have toooons of addressing modes.
    A good reference for them is at:
    https://en.wikipedia.org/wiki/MSP430#MSP430_CPU
    """
    # Normal addressing modes
    DIRECT = 0
    INDEXED = 1
    INDIRECT = 2
    AUTOINCREMENT = 3
    # R0 addressing modes
    SYMBOLIC = 4
    IMMEDIATE = 5
    # R2 (SR) special-case modes
    ABSOLUTE = 6
    CONSTANT4 = 7
    CONSTANT8 = 8
    # R3 (CG) special-case modes
    CONSTANT0 = 9
    CONSTANT1 = 10
    CONSTANT2 = 11
    CONSTANTNEG1 = 12


@unique
class Register(Enum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    R6 = 6
    R7 = 7
    R8 = 8
    R9 = 9
    R10 = 10
    R11 = 11
    R12 = 12
    R13 = 13
    R14 = 14
    R15 = 15


class SingleOperandInstruction:
    def __init__(self, raw, address, opcode, width, addressing_mode, register, operand):
        self.raw = raw
        self.address = address
        self.opcode = opcode
        self.width = width
        self.addressing_mode = addressing_mode
        self.register = register
        self.operand = operand

    def __repr__(self):
        return 'SingleOperandInstruction({!r}, {}, {}, {}, {}, {}, {})'.format(
            self.raw,
            self.address,
            self.opcode,
            self.width,
            self.addressing_mode,
            self.register,
            self.operand)


class JumpInstruction:
    def __init__(self, raw, address, opcode, target):
        self.raw = raw
        self.address = address
        self.opcode = opcode
        self.target = target

    def __repr__(self):
        return 'JumpInstruction({!r}, {}, {}, {})'.format(
            self.raw,
            self.address,
            self.opcode,
            self.target)


class DoubleOperandInstruction:
    def __init__(self, raw, address, opcode, width, source_addressing_mode, \
                 source_register, source_operand, dest_addressing_mode, \
                 dest_register, dest_operand):
        self.raw = raw
        self.address = address
        self.opcode = opcode
        self.width = width
        self.source_addressing_mode = source_addressing_mode
        self.source_register = source_register
        self.source_operand = source_operand
        self.dest_addressing_mode = dest_addressing_mode
        self.dest_register = dest_register
        self.dest_operand = dest_operand

    def __repr__(self):
        return 'DoubleOperandInstruction({!r}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(
            self.raw,
            self.address,
            self.opcode,
            self.width,
            self.source_addressing_mode,
            self.source_register,
            self.source_operand,
            self.dest_addressing_mode,
            self.dest_register,
            self.dest_operand)


def decode_instruction(address, data):
    """
    data is a 24-bit- or 32-bit-long integer


    Reference: http://mspgcc.sourceforge.net/manual/x223.html
               https://en.wikipedia.org/wiki/MSP430#MSP430_CPU
    """

    is_single_operand_instruction = lambda x: (x >> 10) == 0b000100
    is_jump_instruction = lambda x: (x >> 13) == 0b001
    is_double_operand_instruction = lambda x: \
            not is_single_operand_instruction(x) and not is_jump_instruction(x)

    # turn a list of BitVecVals and ints into a list of ints
    unBVV = lambda l: [x.as_long() if is_bv(x) else x for x in data]

    data = unBVV(data)
    instruction = int.from_bytes(data[:2], 'little')

    if is_single_operand_instruction(instruction):
        return decode_single_operand_instruction(address, data)
    elif is_jump_instruction(instruction):
        return decode_jump_instruction(address, data)
    elif is_double_operand_instruction(instruction):
        return decode_double_operand_instruction(address, data)
    else:
        raise ValueError( \
            '0x{:x} does not look like a valid MSP430 instruction!'.format( \
                instruction))


def decode_single_operand_instruction(address, data):
    """
    data is the raw bytes, in little-endian, of at least the area containing
    all information about the current instruction.
    You can give more, but you need at least enough to fully decode the
    instruction, so 6 bytes should be enough.
    top 6 bits are 000100
    """

    instruction = int.from_bytes(data[:2], 'little') # decode instruction

    assert instruction <= 0xFFFF
    assert (instruction >> 10) == 0b000100, \
            'Passed in a non-single operand instruction to decode_single_operand_instruction'


    opcodes = {
        0b000: Opcode.RRC,
        0b001: Opcode.SWPB,
        0b010: Opcode.RRA,
        0b011: Opcode.SXT,
        0b100: Opcode.PUSH,
        0b101: Opcode.CALL,
        0b110: Opcode.RETI,
    }
    def get_opcode(instruction):
        raw = (instruction >> 7) & 0b111
        assert raw in opcodes, 'Invalid Opcode: {}'.format(raw)
        return opcodes[raw]

    widths = {
        0b0: OperandWidth.WORD,
        0b1: OperandWidth.BYTE,
    }
    get_width = lambda x: widths[(x >> 6) & 0b1]

    registers = {
        0b0000: Register.R0,
        0b0001: Register.R1,
        0b0010: Register.R2,
        0b0011: Register.R3,
        0b0100: Register.R4,
        0b0101: Register.R5,
        0b0110: Register.R6,
        0b0111: Register.R7,
        0b1000: Register.R8,
        0b1001: Register.R9,
        0b1010: Register.R10,
        0b1011: Register.R11,
        0b1100: Register.R12,
        0b1101: Register.R13,
        0b1110: Register.R14,
        0b1111: Register.R15,
    }
    get_register = lambda x: registers[(x & 0b1111)]

    normal_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.INDEXED,
        0b10: AddressingMode.INDIRECT,
        0b11: AddressingMode.AUTOINCREMENT,
    }
    r0_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.SYMBOLIC,
        0b10: AddressingMode.INDIRECT,
        0b11: AddressingMode.IMMEDIATE,
    }
    r2_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.ABSOLUTE,
        0b10: AddressingMode.CONSTANT4,
        0b11: AddressingMode.CONSTANT8,
    }
    r3_addressing_modes = {
        0b00: AddressingMode.CONSTANT0,
        0b01: AddressingMode.CONSTANT1,
        0b10: AddressingMode.CONSTANT2,
        0b11: AddressingMode.CONSTANTNEG1,
    }
    def get_addressing_mode(instruction, dest_register):
        mode = (instruction >> 4) & 0b11
        if dest_register == Register.R0: # R0 special
            return r0_addressing_modes[mode]
        elif dest_register == Register.R2: # R2 special
            return r2_addressing_modes[mode]
        elif dest_register == Register.R3: # R3 special
            return r3_addressing_modes[mode]
        else: # normal
            return normal_addressing_modes[mode]

    def get_operand(data, addressing_mode):
        n_bytes = 2

        modes_with_operands = {AddressingMode.IMMEDIATE, \
                AddressingMode.INDEXED, \
                AddressingMode.SYMBOLIC, \
                AddressingMode.ABSOLUTE}
        if addressing_mode in modes_with_operands: # operand is in the instruction stream, extract
            operand = int.from_bytes(data[2:2+n_bytes], 'little')
            operand = BitVecVal(operand, 8 * n_bytes)
            return operand, n_bytes
        else: # no operand
            return None, 0

    opcode = get_opcode(instruction)
    width = get_width(instruction)
    register = get_register(instruction)
    addressing_mode = get_addressing_mode(instruction, register)
    operand, operand_size = get_operand(data, addressing_mode)

    return SingleOperandInstruction(data[:2+operand_size], \
            address, opcode, width, addressing_mode, register, operand), \
            2 + operand_size


def decode_jump_instruction(address, data):
    """
    data is the raw bytes, in little-endian, of at least the area containing
    all information about the current instruction.
    You can give more, but you need at least enough to fully decode the
    instruction, so 6 bytes should be enough.

    top 3 bits of data are 001
    """
    instruction = int.from_bytes(data[:2], 'little') # decode instruction

    assert instruction <= 0xFFFF
    assert (instruction >> 13) == 0b001

    opcodes = {
        0b000: Opcode.JNZ,
        0b001: Opcode.JZ,
        0b010: Opcode.JNC,
        0b011: Opcode.JC,
        0b100: Opcode.JN,
        0b101: Opcode.JGE,
        0b110: Opcode.JL,
        0b111: Opcode.JMP,
    }
    get_opcode = lambda x: opcodes[(instruction >> 10) & 0b111]

    def get_offset(instruction):
        # NOTE: decoded offset is 1/2 the actual offset, so multiply by 2
        magnitude = 2 * (instruction & 0b111111111)
        sign_bit = (instruction >> 9) & 0b1
        if sign_bit == 1:
            return -(2**10 - magnitude) # 2's complement
        else:
            return magnitude

    opcode = get_opcode(instruction)
    offset = get_offset(instruction)
    target = address + 2 + offset # +2 because PC is pre-incremented
    if not is_bv(target): # wrap non-BVs into BVs
        target = BitVecVal(target, 16)

    return JumpInstruction(data[:2], address, opcode, target), 2


def decode_double_operand_instruction(address, data):
    """
    instruction is a 16-bit integer
    argument is an 8- or 16-bit integer, depending on whether the width flag is 0 or 1, respectively
    """
    instruction = int.from_bytes(data[:2], 'little') # decode instruction

    assert instruction <= 0xFFFF

    opcodes = {
        0b0100: Opcode.MOV,
        0b0101: Opcode.ADD,
        0b0110: Opcode.ADDC,
        0b0111: Opcode.SUBC,
        0b1000: Opcode.SUB,
        0b1001: Opcode.CMP,
        0b1010: Opcode.DADD,
        0b1011: Opcode.BIT,
        0b1100: Opcode.BIC,
        0b1101: Opcode.BIS,
        0b1110: Opcode.XOR,
        0b1111: Opcode.AND,
    }
    def get_opcode(instruction):
        raw = (instruction >> 12) & 0b1111
        assert raw in opcodes, 'Invalid opcode for double-operand instruction: {}'.format(raw)
        return opcodes[raw]

    registers = {
        0b0000: Register.R0,
        0b0001: Register.R1,
        0b0010: Register.R2,
        0b0011: Register.R3,
        0b0100: Register.R4,
        0b0101: Register.R5,
        0b0110: Register.R6,
        0b0111: Register.R7,
        0b1000: Register.R8,
        0b1001: Register.R9,
        0b1010: Register.R10,
        0b1011: Register.R11,
        0b1100: Register.R12,
        0b1101: Register.R13,
        0b1110: Register.R14,
        0b1111: Register.R15,
    }
    get_source_register = lambda x: registers[(instruction >> 8) & 0b1111]
    # TODO: check dest registers are movable into (Not R3?)
    get_dest_register = lambda x: registers[instruction & 0b1111]

    normal_source_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.INDEXED,
        0b10: AddressingMode.INDIRECT,
        0b11: AddressingMode.AUTOINCREMENT,
    }
    r0_source_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.SYMBOLIC,
        0b10: AddressingMode.INDIRECT,
        0b11: AddressingMode.IMMEDIATE,
    }
    r2_source_addressing_modes = {
        0b00: AddressingMode.DIRECT,
        0b01: AddressingMode.ABSOLUTE,
        0b10: AddressingMode.CONSTANT4,
        0b11: AddressingMode.CONSTANT8,
    }
    r3_source_addressing_modes = {
        0b00: AddressingMode.CONSTANT0,
        0b01: AddressingMode.CONSTANT1,
        0b10: AddressingMode.CONSTANT2,
        0b11: AddressingMode.CONSTANTNEG1,
    }
    def get_source_addressing_mode(instruction, register):
        raw = (instruction >> 4) & 0b11
        if register == Register.R0:
            return r0_source_addressing_modes[raw]
        elif register == Register.R2:
            return r2_source_addressing_modes[raw]
        elif register == Register.R3:
            return r3_source_addressing_modes[raw]
        else:
            return normal_source_addressing_modes[raw]

    normal_dest_addressing_modes = {
        0b0: AddressingMode.DIRECT,
        0b1: AddressingMode.INDEXED,
    }
    r0_dest_addressing_modes = {
        0b0: AddressingMode.DIRECT,
        0b1: AddressingMode.SYMBOLIC,
    }
    r2_dest_addressing_modes = {
        0b0: AddressingMode.DIRECT,
        0b1: AddressingMode.ABSOLUTE,
    }
    def get_dest_addressing_mode(instruction, register):
        raw = (instruction >> 7) & 0b1
        if register == Register.R0:
            return r0_dest_addressing_modes[raw]
        elif register == Register.R2:
            return r2_dest_addressing_modes[raw]
        else:
            return normal_dest_addressing_modes[raw]

    widths = {
        0b0: OperandWidth.WORD,
        0b1: OperandWidth.BYTE,
    }
    get_operand_width = lambda x: widths[(x >> 6) & 0b1]

    def get_operand(data, addressing_mode, current_offset):
        n_bytes = 2

        modes_with_operands = {AddressingMode.IMMEDIATE, AddressingMode.INDEXED, AddressingMode.ABSOLUTE}
        if addressing_mode in modes_with_operands: # operand is in the instruction stream, extract
            raw = data[current_offset : current_offset + n_bytes]
            operand = int.from_bytes(raw, 'little')
            operand = BitVecVal(operand, 8 * n_bytes)
            return operand, n_bytes
        else: # no operand
            return None, 0

    opcode = get_opcode(instruction)
    source_register = get_source_register(instruction)
    dest_register = get_dest_register(instruction)
    source_addressing_mode = get_source_addressing_mode(instruction, source_register)
    dest_addressing_mode = get_dest_addressing_mode(instruction, dest_register)
    width = get_operand_width(instruction)

    current_offset = 2 # after the instruction
    source_operand, source_size = \
            get_operand(data, source_addressing_mode, current_offset)
    current_offset += source_size # advance instruction stream by the # of bytes we pulled off
    dest_operand, dest_size = \
            get_operand(data, dest_addressing_mode, current_offset)
    current_offset += dest_size

    return DoubleOperandInstruction(data[:2 + current_offset], address, opcode, \
            width, source_addressing_mode, source_register, source_operand, \
            dest_addressing_mode, dest_register, dest_operand), current_offset


def tests():
    """
    Simple, quick checks for some decoding things
    Make these into real unit tests later
    """
    # TODO: Turn these into proper unit tests, expand them.
    # Right now this is really just a spot-check
    print("""
    ################################
    # single operand family checks #
    ################################
            """)

    data = b'\xb0\x12\x58\x45' # should be "call #0x4558"
    instruction, _ = decode_instruction(0x4458, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x00\x13' # should be "reti pc"
    instruction, _ = decode_instruction(0x4584, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x30\x12\x0a\x00' # should be "push 0xa"
    instruction, _ = decode_instruction(0x4572, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x23\x12' # should be "push 0x2"
    instruction, _ = decode_instruction(0x454c, data)
    print('{!r} = {}'.format(data, instruction))

    print("""
    ################################
    #      jump family checks      #
    ################################
            """)

    data = b'\x06\x3c' # should be jmp #0x446a
    instruction, _ = decode_instruction(0x445c, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\xfd\x3f' # should be jmp #0x4470
    instruction, _ = decode_instruction(0x4474, data)
    print('{!r} = {}'.format(data, instruction))

    print("""
    ################################
    # double operand family checks #
    ################################
            """)

    data = b'\x0b\x4f' # should be mov r15, r11
    instruction, _ = decode_instruction(0x455a, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x5f\x44\xfc\xff' # should be mov.b -0x4(r4), r15
    instruction, _ = decode_instruction(0x453a, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x81\x4f\x04\x00' # should be mov r15, 0x4(r1)
    instruction, _ = decode_instruction(0x4512, data)
    print('{!r} = {}'.format(data, instruction))

    data = b'\x9f\x4f\x86\x45\x00\x24' # should be mov 0x4586(r15), 0x2400(r15)
    instruction, _ = decode_instruction(0x441c, data)
    print('{!r} = {}'.format(data, instruction))

if __name__ == '__main__':
    tests()
