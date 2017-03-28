import unittest

from z3 import simplify, BitVecVal

from msp430_symex.state import State, blank_state
from msp430_symex.code import decode_instruction

def intval(v):
    if isinstance(v, int):
        return v
    return simplify(v).as_long()

# TODO: Test these!!
"""
RRC
"""

class TestSwpbInstruction(unittest.TestCase):

    def test_instruction_semantics_swpb(self):
        # swpb r6
        raw = b'\x86\x10'
        ip = 0x1234

        ins, _ = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R6'] = BitVecVal(0xdead, 16)

        new_states = state.cpu.step_swpb(state, ins)
        
        self.assertEqual(len(new_states), 1)

        new_state = new_states[0]
        self.assertEqual(intval(new_state.cpu.registers['R6']), 0xadde)


# TODO: Test these!!
"""
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
"""

class TestJcInstruction(unittest.TestCase):

    def test_instruction_semantics_jc(self):
        # jc #0x1446
        raw = b'\x08\x2d'
        ip = 0x1234

        ins, ins_len = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R0'] = ip + ins_len # ip is always preincremented

        expected_taken = 0x1446
        expected_not_taken = 0x1236

        new_states = state.cpu.step_jc(state, ins)

        self.assertEqual(len(new_states), 2)

        taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_taken]
        not_taken_states = [st for st in new_states if intval(st.cpu.registers['R0']) == expected_not_taken]

        self.assertEqual(len(taken_states), 1)
        self.assertEqual(len(not_taken_states), 1)


#TODO: Test these!!
"""
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


class TestMovInstruction(unittest.TestCase):

    def test_instruction_semantics_mov(self):
        # mov #0xdead, r6
        raw = b'\x36\x40\xad\xde'
        ip = 0x1234

        ins, _ = decode_instruction(ip, raw)

        state = blank_state()

        new_states = state.cpu.step_mov(state, ins)

        self.assertEqual(len(new_states), 1)
        
        new_state = new_states[0]
        self.assertEqual(intval(new_state.cpu.registers['R6']), 0xdead)


# TODO: Test these!!
"""
ADD
ADDC
SUBC
SUB
CMP
DADD
BIT
"""

class TestBicInstruction(unittest.TestCase):

    def test_instruction_semantics_bic(self):
        # bic #0x0f0f, r6
        raw = b'\x36\xc0\x0f\x0f'
        ip = 0x1234

        ins, _ = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R6'] = BitVecVal(0xdead, 16)

        new_states = state.cpu.step_bic(state, ins)

        self.assertEqual(len(new_states), 1)
        new_state = new_states[0]

        self.assertEqual(intval(new_state.cpu.registers['R6']), 0xd0a0)


class TestBisInstruction(unittest.TestCase):

    def test_instruction_semantics_bis(self):
        # bis #0x0f0f, r6
        raw = b'\x36\xd0\x0f\x0f'
        ip = 0x1234

        ins, _ = decode_instruction(ip, raw)

        state = blank_state()
        state.cpu.registers['R6'] = BitVecVal(0xdead, 16)

        new_states = state.cpu.step_bis(state, ins)

        self.assertEqual(len(new_states), 1)
        new_state = new_states[0]

        self.assertEqual(intval(new_state.cpu.registers['R6']), 0xdfaf)
        

# TODO: Test these!!
"""
XOR
AND
"""

if __name__ == '__main__':
    unittest.main()
