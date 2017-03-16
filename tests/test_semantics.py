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

    def test_single_operand_autoincrement(self):
        # push @r15
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

    def test_single_operand_constant4(self):
        # push #4
        raw = b'\x22\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x4)

    def test_single_operand_constant8(self):
        # push #8
        raw = b'\x32\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
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

        cpu = CPU()
        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x0)

    def test_single_operand_constant1(self):
        # push #1
        raw = b'\x13\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x1)

    def test_single_operand_constant2(self):
        # push #1
        raw = b'\x23\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x2)

    def test_single_operand_constantneg1(self):
        # push #-1
        raw = b'\x33\x12'
        addr = BitVecVal(0x0, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        state = blank_state()

        operand = state.cpu.get_single_operand_value(state, ins)
        operand = operand.as_signed_long() # unwrap Z3 value

        self.assertEqual(operand, -1)


if __name__ == '__main__':
    unittest.main()
