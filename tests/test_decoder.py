import unittest
from msp430_symex.code import decode_instruction, DoubleOperandInstruction, \
        SingleOperandInstruction, JumpInstruction, Opcode, OperandWidth, \
        AddressingMode, Register


class TestCallDecode(unittest.TestCase):

    def test_call_decode(self):
        raw = b'\xb0\x12\x58\x45'
        ip = 0x4458

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.CALL)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.IMMEDIATE)
        self.assertEqual(instruction.operand, 0x4558)

class TestRetiDecode(unittest.TestCase):

    def test_reti_decode(self):
        # should be "reti pc"
        raw = b'\x00\x13'
        ip = 0x4484

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.RETI)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.register, Register.R0)
        self.assertEqual(instruction.operand, None)

class TestPushImmDecode(unittest.TestCase):

    def test_push_immediate_decode(self):
        # should be "push 0xa"
        raw = b'\x30\x12\x0a\x00'
        ip = 0x4472

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.PUSH)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.IMMEDIATE)
        self.assertEqual(instruction.operand, 0xa)

class TestPushConstGenDecode(unittest.TestCase):

    def test_push_constant_generator_decode(self):
        # should be "push 0x2"
        raw = b'\x23\x12'
        ip = 0x454c

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.PUSH)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.CONSTANT2)
        self.assertEqual(instruction.register, Register.R3)
        self.assertEqual(instruction.operand, None)

if __name__ == '__main__':
    unittest.main()
