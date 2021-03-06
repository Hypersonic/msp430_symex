import unittest
from z3 import simplify

from msp430_symex.code import decode_instruction, DoubleOperandInstruction, \
        SingleOperandInstruction, JumpInstruction, Opcode, OperandWidth, \
        AddressingMode, Register


class TestSingleOperandDecode(unittest.TestCase):

    def test_call_decode(self):
        raw = b'\xb0\x12\x58\x45'
        ip = 0x4458

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.CALL)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.IMMEDIATE)
        operand = instruction.operand
        operand = simplify(operand).as_long()
        self.assertEqual(operand, 0x4558)

    def test_reti_decode(self):
        # should be "reti pc"
        raw = b'\x00\x13'
        ip = 0x4484

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.RETI)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.register, Register.R0)
        self.assertEqual(instruction.operand, None)

    def test_call_symbolic_decode(self):
        # call 0x1234
        # (or call 0x1234(r0))
        raw = b'\x90\x12\x32\x12'
        ip = 0xc0de

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')

        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.CALL)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.SYMBOLIC)
        self.assertEqual(instruction.register, Register.R0)
        # 0x1232 instead of 0x1234 because -2 from instruction width
        operand = instruction.operand
        operand = simplify(operand).as_long()
        self.assertEqual(operand, 0x1232)

    def test_call_absolute_decode(self):
        # call &0x1234
        raw = b'\x92\x12\x34\x12'
        ip = 0xc0de

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')

        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.CALL)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.ABSOLUTE)
        self.assertEqual(instruction.register, Register.R2)
        operand = instruction.operand
        operand = simplify(operand).as_long()
        self.assertEqual(operand, 0x1234)

    def test_push_immediate_decode(self):
        # should be "push 0xa"
        raw = b'\x30\x12\x0a\x00'
        ip = 0x4472

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, SingleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.PUSH)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.addressing_mode, AddressingMode.IMMEDIATE)
        operand = instruction.operand
        operand = simplify(operand).as_long()
        self.assertEqual(operand, 0xa)

    def test_push_constant_generator_decode(self):
        # should be "push 0x2"
        raw = b'\x23\x12'
        ip = 0x454c

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
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

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, JumpInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.JMP)
        target = instruction.target
        target = simplify(target).as_long()
        self.assertEqual(target, 0x446a)

    def test_jnz_decode(self):

        raw = b'\xf9\x23' # should be jnz #0x4416
        ip = 0x4422

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, JumpInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.JNZ)
        target = instruction.target
        target = simplify(target).as_long()
        self.assertEqual(target, 0x4416)

    def test_jz_decode(self):

        raw = b'\x06\x24' # should be jz #0x4438
        ip = 0x442a

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, JumpInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.JZ)
        target = instruction.target
        target = simplify(target).as_long()
        self.assertEqual(target, 0x4438)


class TestDoubleOperandDecode(unittest.TestCase):

    def test_mov_symbolic_decode(self):
        # mov 0x2400, r1
        raw = b'\x11\x40\xfe\x23'
        ip = 0xc0de

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, DoubleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.MOV)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.source_addressing_mode, AddressingMode.SYMBOLIC)
        self.assertEqual(instruction.source_register, Register.R0)
        source_operand = instruction.source_operand
        source_operand = source_operand.as_long()
        self.assertEqual(source_operand, 0x2400 - 2)
        self.assertEqual(instruction.dest_addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.dest_register, Register.R1)
        self.assertEqual(instruction.dest_operand, None)

    def test_mov_reg_reg_decode(self):
        raw = b'\x0b\x4f' # should be mov r15, r11
        ip = 0x455a

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
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

    def test_mov_offset_reg_decode(self):
        raw = b'\x5f\x44\xfc\xff' # should be mov.b -0x4(r4), r15
        ip = 0x453a

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, DoubleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.MOV)
        self.assertEqual(instruction.width, OperandWidth.BYTE)
        self.assertEqual(instruction.source_addressing_mode, AddressingMode.INDEXED)
        self.assertEqual(instruction.source_register, Register.R4)
        source_operand = instruction.source_operand
        source_operand = simplify(source_operand).as_signed_long()
        self.assertEqual(source_operand, -0x4)
        self.assertEqual(instruction.dest_addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.dest_register, Register.R15)
        self.assertEqual(instruction.dest_operand, None)

    def test_mov_reg_offset_decode(self):

        raw = b'\x81\x4f\x04\x00' # should be mov r15, 0x4(r1)
        ip = 0x4512

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, DoubleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.MOV)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.source_addressing_mode, AddressingMode.DIRECT)
        self.assertEqual(instruction.source_register, Register.R15)
        self.assertEqual(instruction.source_operand, None)
        self.assertEqual(instruction.dest_addressing_mode, AddressingMode.INDEXED)
        self.assertEqual(instruction.dest_register, Register.R1)
        dest_operand = instruction.dest_operand
        dest_operand = simplify(dest_operand).as_signed_long()
        self.assertEqual(dest_operand, 0x4)

    def test_mov_offset_offset_decode(self):
        raw = b'\x9f\x4f\x86\x45\x00\x24' # should be mov 0x4586(r15), 0x2400(r15)
        ip = 0x441c

        instruction, _ = decode_instruction(ip, raw + b'\xFF\xFF\xFF')
        self.assertIsInstance(instruction, DoubleOperandInstruction)
        self.assertEqual(instruction.raw, list(raw))
        self.assertEqual(instruction.opcode, Opcode.MOV)
        self.assertEqual(instruction.width, OperandWidth.WORD)
        self.assertEqual(instruction.source_addressing_mode, AddressingMode.INDEXED)
        self.assertEqual(instruction.source_register, Register.R15)
        source_operand = instruction.source_operand
        source_operand = simplify(source_operand).as_signed_long()
        self.assertEqual(source_operand, 0x4586)
        self.assertEqual(instruction.dest_addressing_mode, AddressingMode.INDEXED)
        self.assertEqual(instruction.dest_register, Register.R15)
        dest_operand = instruction.dest_operand
        dest_operand = simplify(dest_operand).as_signed_long()
        self.assertEqual(dest_operand, 0x2400)


if __name__ == '__main__':
    unittest.main()
