import unittest

from z3 import BitVecVal, simplify

from msp430_symex.code import Opcode, OperandWidth, Register, AddressingMode, \
        SingleOperandInstruction, DoubleOperandInstruction, JumpInstruction, \
        decode_instruction
from msp430_symex.cpu import RegisterFile, DestinationType, CPU
from msp430_symex.state import State
from msp430_symex.memory import Memory

def blank_state():
    # TODO: initialize stuff to sane non-None values
    cpu = CPU()
    memory_data = [BitVecVal(0, 8) for _ in range(0xFFFF)]
    memory = Memory(memory_data)
    return State(cpu, memory, None, None, None, False)


class TestGetSingleOperandValue(unittest.TestCase):
    
    def test_single_operand_direct(self):
        # swp.b r15
        raw = b'\x8f\x10'
        addr = BitVecVal(0x44fc, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x1234)

    def test_single_operand_direct_byte(self):
        # rra.b r15
        raw = b'\x4f\x11'
        addr = BitVecVal(0x44fc, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x34)

    def test_single_operand_indexed(self):
        # push 0x2400(r15)
        raw = b'\x1f\x12\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location (high and low separately)
        state.memory[0x2400 + 0x1234] = BitVecVal(0xad, 8)
        state.memory[0x2400 + 0x1234+1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xdead)

    def test_single_operand_indexed_byte(self):
        # rra.b 0x2400(r15)
        raw = b'\x5f\x11\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location
        state.memory[0x2400 + 0x1234] = BitVecVal(0xc0, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xc0)

    def test_single_operand_indirect(self):
        # push @r15
        raw = b'\x2f\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location (high and low separately)
        state.memory[0x1234] = BitVecVal(0xad, 8)
        state.memory[0x1234 + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xdead)

    def test_single_operand_indirect_byte(self):
        # rra.b @r15
        raw = b'\x6f\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location
        state.memory[0x1234] = BitVecVal(0xc0, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xc0)


    def test_single_operand_autoincrement(self):
        # push @r15+
        raw = b'\x3f\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location (high and low separately)
        state.memory[0x1234] = BitVecVal(0xad, 8)
        state.memory[0x1234 + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        new_reg = state.cpu.registers['R15']
        new_reg = simplify(new_reg).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xdead)
        self.assertEqual(new_reg, 0x1236)

    def test_single_operand_autoincrement_byte(self):
        # rra.b @r15+
        raw = b'\x7f\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15

        # put known val in memory location
        state.memory[0x1234] = BitVecVal(0xc0, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        new_reg = state.cpu.registers['R15']
        new_reg = simplify(new_reg).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xc0)
        self.assertEqual(new_reg, 0x1235)

    def test_single_operand_symbolic(self):
        # call 0x1234
        # (or call 0x1234(r0))
        raw = b'\x90\x12\x32\x12'
        addr = BitVecVal(0xc0de, 16)
        ins, _ = decode_instruction(addr, raw)

        stored_addr = 0x1232 + 0xc0de # where things are stored (ip + imm - 2)
        state = blank_state()
        state.cpu.registers['R0'] = addr

        # put known val in memory location
        state.memory[stored_addr] = BitVecVal(0xad, 8)
        state.memory[stored_addr + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xdead)
        
    def test_single_operand_symbolic_byte(self):
        # rra.b 0x1234
        raw = b'\x50\x11\x32\x12'
        addr = BitVecVal(0xc0de, 16)
        ins, _ = decode_instruction(addr, raw)

        stored_addr = 0x1232 + 0xc0de # where things are stored (ip + imm - 2)
        state = blank_state()
        state.cpu.registers['R0'] = addr

        # put known val in memory location
        state.memory[stored_addr] = BitVecVal(0xd0, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xd0)

    def test_single_operand_immediate(self):
        # call #0x4558
        raw = b'\xb0\x12\x58\x45'
        addr = BitVecVal(0x4440, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R0'] = addr

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x4558)

    def test_single_operand_immediate_byte(self):
        # rra.b #0x1234
        raw = b'\x70\x11\x34\x12'
        addr = BitVecVal(0x4440, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R0'] = addr

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x34) # we should only get back the low byte

    # R2 (SR) special-case modes

    def test_single_operand_absolute(self):
        # call &0x1234
        raw = b'\x92\x12\x34\x12'
        addr = BitVecVal(0xc0de, 16)
        ins, _ = decode_instruction(addr, raw)

        stored_addr = 0x1234
        state = blank_state()

        # put known val in memory location
        state.memory[stored_addr] = BitVecVal(0xad, 8)
        state.memory[stored_addr + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xdead)

    def test_single_operand_absolute_byte(self):
        # rra.b &0x1234
        raw = b'\x52\x11\x34\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        stored_addr = 0x1234
        state = blank_state()

        # put known val in memory location
        state.memory[stored_addr] = BitVecVal(0xc0, 8)

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = simplify(operand).as_long() # unwrap Z3 value

        self.assertEqual(operand, 0xc0)

    def test_single_operand_constant4(self):
        # push #4
        raw = b'\x22\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x4)

    def test_single_operand_constant4_byte(self):
        # rra.b #4
        raw = b'\x62\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x4)

    def test_single_operand_constant8(self):
        # push #8
        raw = b'\x32\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x8)

    def test_single_operand_constant8_byte(self):
        # rra.b #4
        raw = b'\x72\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x8)

    # R3 (CG) special-case modes

    def test_single_operand_constant0(self):
        # push #0
        raw = b'\x03\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x0)

    def test_single_operand_constant0_byte(self):
        # rra.b #0
        raw = b'\x43\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x0)

    def test_single_operand_constant1(self):
        # push #1
        raw = b'\x13\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x1)

    def test_single_operand_constant1_byte(self):
        # rra.b #1
        raw = b'\x53\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x1)

    def test_single_operand_constant2(self):
        # push #1
        raw = b'\x23\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x2)

    def test_single_operand_constant2_byte(self):
        # rra.b #1
        raw = b'\x63\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x2)

    def test_single_operand_constantneg1(self):
        # push #-1
        raw = b'\x33\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_signed_long() # unwrap Z3 value

        self.assertEqual(operand, -1)

    def test_single_operand_constantneg1_byte(self):
        # rra.b #-1
        raw = b'\x73\x11'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_signed_long() # unwrap Z3 value

        self.assertEqual(operand, -1)

class TestGetDoubleOperandSourceValue(unittest.TestCase):

    def test_double_operand_source_direct(self):
        # mov r15, r1
        raw = b'\x01\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = operand.as_long()

        self.assertEqual(operand, 0xbeef)

    def test_double_operand_source_direct_byte(self):
        # mov.b r15, r1
        raw = b'\x41\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xef)

    def test_double_operand_source_indexed(self):
        # mov 0x2400(r15), r1
        raw = b'\x11\x4f\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0x2400 + 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)
        state.memory[src_loc + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xdead)

    def test_double_operand_source_indexed_byte(self):
        # mov.b 0x2400(r15), r1
        raw = b'\x51\x4f\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0x2400 + 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xad)

    def test_double_operand_source_indirect(self):
        # mov @r15, r1
        raw = b'\x21\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)
        state.memory[src_loc + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xdead)

    def test_double_operand_source_indirect_byte(self):
        # mov.b @r15, r1
        raw = b'\x61\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xad)

    def test_double_operand_source_autoincrement(self):
        # mov @r15+, r1
        raw = b'\x31\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)
        state.memory[src_loc + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        new_reg = state.cpu.registers['R15']
        new_reg = simplify(new_reg).as_long()

        self.assertEqual(operand, 0xdead)
        self.assertEqual(new_reg, 0xbef1)

    def test_double_operand_source_autoincrement_byte(self):
        # mov.b @r15+, r1
        raw = b'\x71\x4f'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0xbeef, 16)

        src_loc = 0xbeef
        state.memory[src_loc] = BitVecVal(0xad, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        new_reg = state.cpu.registers['R15']
        new_reg = simplify(new_reg).as_long()

        self.assertEqual(operand, 0xad)
        self.assertEqual(new_reg, 0xbef0)

    def test_double_operand_source_symbolic(self):
        # mov 0x2400, r1
        raw = b'\x11\x40\xfe\x23'
        addr = BitVecVal(0xc0de, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R0'] = BitVecVal(0xc0de, 16)
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        src_loc = 0x2400 + 0xc0de - 2
        state.memory[src_loc] = BitVecVal(0xad, 8)
        state.memory[src_loc + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xdead)

    def test_double_operand_source_symbolic_byte(self):
        # mov.b 0x2400, r1
        raw = b'\x51\x40\xfe\x23'
        addr = BitVecVal(0xc0de, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R0'] = BitVecVal(0xc0de, 16)
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        src_loc = 0x2400 + 0xc0de - 2
        state.memory[src_loc] = BitVecVal(0xad, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xad)

    def test_double_operand_source_immediate(self):
        # mov #0xdead, r1
        raw = b'\x31\x40\xad\xde'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xdead)

    def test_double_operand_source_immediate_byte(self):
        # mov.b #0xdead, r1
        raw = b'\x71\x40\xad\xde'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xad)

    def test_double_operand_source_absolute(self):
        # mov &2400, r1
        raw = b'\x11\x42\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        src_loc = 0x2400
        state.memory[src_loc] = BitVecVal(0xad, 8)
        state.memory[src_loc + 1] = BitVecVal(0xde, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xdead)

    def test_double_operand_source_absolute_byte(self):
        # mov.b &2400, r1
        raw = b'\x51\x42\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        src_loc = 0x2400
        state.memory[src_loc] = BitVecVal(0xad, 8)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0xad)

    def test_double_operand_source_constant4(self):
        # mov #4, r1
        raw = b'\x21\x42'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x4)

    def test_double_operand_source_constant4_byte(self):
        # mov.b #4, r1
        raw = b'\x61\x42'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x4)

    def test_double_operand_source_constant8(self):
        # mov #8, r1
        raw = b'\x31\x42'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x8)

    def test_double_operand_source_constant8_byte(self):
        # mov.b #8, r1
        raw = b'\x71\x42'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x8)

    def test_double_operand_source_constant0(self):
        # mov #0, r1
        raw = b'\x01\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x0)

    def test_double_operand_source_constant0_byte(self):
        # mov.b #0, r1
        raw = b'\x41\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x0)

    def test_double_operand_source_constant1(self):
        # mov #1, r1
        raw = b'\x11\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x1)

    def test_double_operand_source_constant1_byte(self):
        # mov.b #1, r1
        raw = b'\x51\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x1)

    def test_double_operand_source_constant2(self):
        # mov #2, r1
        raw = b'\x21\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x2)

    def test_double_operand_source_constant2_byte(self):
        # mov.b #2, r1
        raw = b'\x61\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_long()

        self.assertEqual(operand, 0x2)

    def test_double_operand_source_constantneg1(self):
        # mov #-1, r1
        raw = b'\x31\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_signed_long()

        self.assertEqual(operand, -0x1)

    def test_double_operand_source_constantneg1_byte(self):
        # mov.b #-1, r1
        raw = b'\x71\x43'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        operand = state.cpu.get_double_operand_source_value(state, ins)
        operand = simplify(operand).as_signed_long()

        self.assertEqual(operand, -0x1)


class TestGetDoubleOperandDestLocation(unittest.TestCase):

    def test_double_operand_dest_direct(self):
        # mov r1, r15
        raw = b'\x0f\x41'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16)

        dest, dest_type = state.cpu.get_double_operand_dest_location(state, ins)

        self.assertEqual(dest, Register.R15)
        self.assertEqual(dest_type, DestinationType.REGISTER)

    def test_double_operand_dest_indexed(self):
        # mov r1, 0x2400(r15)
        raw = b'\x8f\x41\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R15'] = BitVecVal(0x1234, 16)

        dest, dest_type = state.cpu.get_double_operand_dest_location(state, ins)
        dest = simplify(dest).as_long()

        self.assertEqual(dest, 0x2400 + 0x1234)
        self.assertEqual(dest_type, DestinationType.ADDRESS)

    def test_double_operand_dest_symbolic(self):
        # mov r1, 0x2400
        raw = b'\x80\x41\xfe\x23'
        addr = BitVecVal(0x1234, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R0'] = BitVecVal(0x1234, 16)
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        dest, dest_type = state.cpu.get_double_operand_dest_location(state, ins)
        dest = simplify(dest).as_long()

        self.assertEqual(dest, 0x2400 + 0x1234 - 2)
        self.assertEqual(dest_type, DestinationType.ADDRESS)

    def test_double_operand_dest_absolute(self):
        # mov r1, &0x2400
        raw = b'\x82\x41\x00\x24'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(0x1234, 16)

        dest, dest_type = state.cpu.get_double_operand_dest_location(state, ins)
        dest = simplify(dest).as_long()

        self.assertEqual(dest, 0x2400)
        self.assertEqual(dest_type, DestinationType.ADDRESS)


if __name__ == '__main__':
    unittest.main()
