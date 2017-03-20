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


if __name__ == '__main__':
    unittest.main()
