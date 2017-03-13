import unittest
from msp430_symex.code import decode_instruction, DoubleOperandInstruction, \
        SingleOperandInstruction, JumpInstruction, Opcode, OperandWidth, \
        AddressingMode


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

if __name__ == '__main__':
    unittest.main()
