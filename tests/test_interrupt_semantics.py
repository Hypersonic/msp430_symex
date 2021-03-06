import unittest

from z3 import BitVecVal

from msp430_symex.state import blank_state


class TestPutcharInterrupt(unittest.TestCase):
    
    def test_interrupt_putchar(self):
        ARG_OFFSET = 6
        STACK_LOC = 0x1234
        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(STACK_LOC, 16)

        state.memory[STACK_LOC + ARG_OFFSET] = BitVecVal(0x41, 8)

        new_states = state.cpu.int_putchar(state)

        self.assertEqual(len(new_states), 1)

        new_state = new_states[0]

        output = new_state.sym_output.dump(new_state)
        
        self.assertEqual(output, b'A')


# waiting on getchar implementation
"""
class TestGetcharInterrupt(unittest.TestCase):
    
    def test_interrupt_getchar(self):
        pass
"""

class TestGetsInterrupt(unittest.TestCase):

    def test_interrupt_gets(self):
        ARG_OFFSET = 6
        STACK_LOC = 0x1234
        state = blank_state()
        state.cpu.registers['R1'] = BitVecVal(STACK_LOC, 16)

        addr = 0xc0de
        length = 0x000f
        state.memory[STACK_LOC + ARG_OFFSET] = BitVecVal(addr & 0xFF, 8)
        state.memory[STACK_LOC + ARG_OFFSET + 1] = BitVecVal((addr >> 8) & 0xFF, 8)

        state.memory[STACK_LOC + ARG_OFFSET + 2] = BitVecVal(length & 0xFF, 8)
        state.memory[STACK_LOC + ARG_OFFSET + 3] = BitVecVal((length >> 8) & 0xFF, 8)

        new_states = state.cpu.int_gets(state)

        self.assertEqual(len(new_states), 1)

        new_state = new_states[0]

        inp_data = new_state.sym_input.data
        inp_data_in_memory = new_state.memory[addr : addr + length]

        self.assertEqual(len(inp_data), length)
        self.assertEqual(len(inp_data_in_memory), length)
        self.assertEqual(inp_data, inp_data_in_memory)


# Waiting on implementation:
"""
int_enabledep
int_setpageperms
int_rand
"""

class TestHSM1Interrupt(unittest.TestCase):

    def test_interrupt_hsm1(self):
        """
        Because the HSM1 check can never pass, 
        this just calls the HSM1 interrupt to make sure it does not error,
        and returns 1 state.
        """
        state = blank_state()
        new_states = state.cpu.int_hsm1check(state)

        self.assertEqual(len(new_states), 1)


class TestHSM2Interrupt(unittest.TestCase):

    def test_interrupt_hsm2(self):
        """
        Because the HSM2 check can never pass, 
        this just calls the HSM2 interrupt to make sure it does not error,
        and returns 1 state.
        """
        state = blank_state()
        new_states = state.cpu.int_hsm2check(state)

        self.assertEqual(len(new_states), 1)


class TestUnlockInterrupt(unittest.TestCase):

    def test_interrupt_unlock(self):
        state = blank_state()
        new_states = state.cpu.int_unlock(state)

        self.assertEqual(len(new_states), 1)

        new_state = new_states[0]
        
        self.assertTrue(new_state.unlocked)


if __name__ == '__main__':
    unittest.main()
