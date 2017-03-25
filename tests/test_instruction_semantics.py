import unittest

from z3 import simplify

from msp430_symex.state import State, blank_state
from msp430_symex.code import decode_instruction

def intval(v):
    if isinstance(v, int):
        return v
    return simplify(v).as_long()

# TODO: Test these!!
"""
RRC
SWPB
RRA
SXT
PUSH
CALL
RETI
"""

class TestJnzInstruction(unittest.TestCase):

    def test_instruction_semantics_jnz(self):
        # jnz #0x1446
        raw = b'\x08\x21'
        ip = 0x1234

        ins, ins_len = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R0'] = ip + ins_len # ip is always preincremented

        expected_taken = 0x1446
        expected_not_taken = 0x1236

        new_states = state.cpu.step_jnz(state, ins)

        self.assertEqual(len(new_states), 2)

        taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_taken]
        not_taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_not_taken]

        self.assertEqual(len(taken_states), 1)
        self.assertEqual(len(not_taken_states), 1)


class TestJzInstruction(unittest.TestCase):

    def test_instruction_semantics_jz(self):
        # jz #0x1446
        raw = b'\x08\x25'
        ip = 0x1234

        ins, ins_len = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R0'] = ip + ins_len # ip is always preincremented

        expected_taken = 0x1446
        expected_not_taken = 0x1236

        new_states = state.cpu.step_jz(state, ins)

        self.assertEqual(len(new_states), 2)

        taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_taken]
        not_taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_not_taken]

        self.assertEqual(len(taken_states), 1)
        self.assertEqual(len(not_taken_states), 1)

# TODO: Test these!!
"""
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
