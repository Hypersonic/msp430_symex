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


class TestJmpDecode(unittest.TestCase):

    def test_jmp_decode(self):
        # should be jmp #0x446a
        raw = b'\x06\x3c'
        ip = 0x445c

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, JumpInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.JMP)
        self.assertEqual(instruction.target, 0x446a)


class TestMovRegRegDecode(unittest.TestCase):

    def test_mov_reg_reg_decode(self):
        raw = b'\x0b\x4f' # should be mov r15, r11
        ip = 0x455a

        instruction, _ = decode_instruction(ip, raw)
        self.assertIsInstance(instruction, DoubleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.MOV)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.source_addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.source_register, Register.R15)
        self.assertEqual(instruction.source_operand, None)
        self.assertEqual(instruction.dest_addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.dest_register, Register.R11)
        self.assertEqual(instruction.dest_operand, None)


if __name__ == '__main__':
    unittest.main()
