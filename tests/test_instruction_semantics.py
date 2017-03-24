import unittest

from z3 import simplify

from msp430_symex.state import State, blank_state
from msp430_symex.code import decode_instruction

# TODO: Test these!!
"""
RRC
SWPB
RRA
SXT
PUSH
CALL
RETI
JNZ
JZ
JNC
JC
JN
JGE
JL
"""

class TestJmpInstruction(unittest.TestCase):
    
    def test_instruction_semantics_jmp(self):
        # should be jmp #0x446a
        raw = b'\x06\x3c'
        ip = 0x445c

        ins, _ = decode_instruction(ip, raw)

        state = blank_state()

        new_states = state.cpu.step_jmp(state, ins)

        self.assertEqual(len(new_states), 1)
        new_ip = new_states[0].cpu.registers['R0']
        new_ip = simplify(new_ip).as_long()
        self.assertEqual(new_ip, 0x446a)

# TODO: Test these!!
"""
MOV
ADD
ADDC
SUBC
SUB
CMP
DADD
BIT
BIC
BIS
XOR
AND
"""

if __name__ == '__main__':
    unittest.main()
