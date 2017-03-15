import unittest

from z3 import BitVecVal

from msp430_symex.code import Opcode, OperandWidth, Register, AddressingMode, \
        SingleOperandInstruction, DoubleOperandInstruction, JumpInstruction, \
        decode_instruction
from msp430_symex.cpu import RegisterFile, DestinationType, CPU 
from msp430_symex.state import State

def state_with_cpu(cpu):
    # TODO: initialize stuff to sane non-None values
    return State(cpu, None, None, None, None, False)

class TestGetSingleOperandValue(unittest.TestCase):
    
    def test_single_operand_immediate(self):
        # call 0x4558
        raw = b'\xb0\x12\x58\x45'
        addr = BitVecVal(0x4440, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        cpu.registers['R0'] = addr
        state = state_with_cpu(cpu)

        operand = cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x4558)

    def test_single_operand_register(self):
        # swp.b r15
        raw = b'\x8f\x10'
        addr = BitVecVal(0x44fc, 16)
        ins, _ = decode_instruction(addr, raw)

        cpu = CPU()
        cpu.registers['R0'] = addr
        cpu.registers['R15'] = BitVecVal(0x1234, 16) # put known val into R15
        state = state_with_cpu(cpu)

        operand = cpu.get_single_operand_value(state, ins)
        operand = operand.as_long() # unwrap Z3 value

        self.assertEqual(operand, 0x1234)


if __name__ == '__main__':
    unittest.main()
