from enum import Enum, unique
from z3 import BitVecVal, Concat, Extract, And, Or, Not, simplify, If

from .code import Register, Opcode, OperandWidth, AddressingMode, \
        SingleOperandInstruction, JumpInstruction, DoubleOperandInstruction


@unique
class DestinationType(Enum):
    """
    The type of a destination operand while executing instructions
    """
    REGISTER = 0
    ADDRESS = 1

class RegisterFile:
    """
    All the registers, plus their values
    """
    reg_strs = {
        'R0': Register.R0,
        'R1': Register.R1,
        'R2': Register.R2,
        'R3': Register.R3,
        'R4': Register.R4,
        'R5': Register.R5,
        'R6': Register.R6,
        'R7': Register.R7,
        'R8': Register.R8,
        'R9': Register.R9,
        'R10': Register.R10,
        'R11': Register.R11,
        'R12': Register.R12,
        'R13': Register.R13,
        'R14': Register.R14,
        'R15': Register.R15,
    }
    reg_nums = {
        0: Register.R0,
        1: Register.R1,
        2: Register.R2,
        3: Register.R3,
        4: Register.R4,
        5: Register.R5,
        6: Register.R6,
        7: Register.R7,
        8: Register.R8,
        9: Register.R9,
        10: Register.R10,
        11: Register.R11,
        12: Register.R12,
        13: Register.R13,
        14: Register.R14,
        15: Register.R15,
    }

    def __init__(self, set_regs={}):
        self.registers = {
            Register.R0: BitVecVal(0, 16),
            Register.R1: BitVecVal(0, 16),
            Register.R2: BitVecVal(0, 16),
            Register.R3: BitVecVal(0, 16),
            Register.R4: BitVecVal(0, 16),
            Register.R5: BitVecVal(0, 16),
            Register.R6: BitVecVal(0, 16),
            Register.R7: BitVecVal(0, 16),
            Register.R8: BitVecVal(0, 16),
            Register.R9: BitVecVal(0, 16),
            Register.R10: BitVecVal(0, 16),
            Register.R11: BitVecVal(0, 16),
            Register.R12: BitVecVal(0, 16),
            Register.R13: BitVecVal(0, 16),
            Register.R14: BitVecVal(0, 16),
            Register.R15: BitVecVal(0, 16),
        }

        self.registers.update(set_regs)

        # bitmasks for SR (R2)
        self.mask_C = 0b1
        self.mask_Z = 0b10
        self.mask_N = 0b100
        self.mask_V = 0b10000000

    def __getitem__(self, key):
        if isinstance(key, str):
            key = RegisterFile.reg_strs[key.upper()]
        elif isinstance(key, int):
            key = RegisterFile.reg_nums[key]
        return self.registers[key]

    def __setitem__(self, key, value):
        if isinstance(key, str):
            key = RegisterFile.reg_strs[key.upper()]
        elif isinstance(key, int):
            key = RegisterFile.reg_nums[key]
        self.registers[key] = value

    def __repr__(self):
        return 'RegisterFile({})'.format(self.registers)

    def clone(self):
        return RegisterFile(self.registers)


class CPU:
    def __init__(self, registers=None):
        if registers is None:
            registers = RegisterFile()

        self.registers = registers

        self.interrupt_address = 0x10 # callgated addr for interrupts

        # interrupt id -> summary function
        self.interrupts = {
            0x00: self.int_putchar,
            0x01: self.int_getchar,
            0x02: self.int_gets,
            0x10: self.int_enabledep,
            0x11: self.int_setpageperms,
            0x20: self.int_rand,
            0x7d: self.int_hsm1check,
            0x7e: self.int_hsm2check,
            0x7f: self.int_unlock,
        }

    def clone(self):
        return self.__class__(self.registers.clone())

    def push(self, state, value):
        """
        Push value onto the stack in state
        """
        state.cpu.registers[Register.R1] -= 2
        address = state.cpu.registers[Register.R1]
        state.memory[address] = Extract(7, 0, value)
        state.memory[address+1] = Extract(15, 8, value)

    def pop(self, state):
        """
        Pop a value from the stack, return it
        """
        address = state.cpu.registers[Register.R1]
        low = state.memory[address]
        high = state.memory[address+1]
        val = Concat(high, low)

        state.cpu.registers[Register.R1] += 2

        return val


    def get_single_operand_value(self, state, instruction):
        """
        Get the operand value for a single-operand instruction

        NOTE: not pure!!! may modify a register if the addressing mode is
        AUTOINCREMENT
        """
        #XXX: Consider moving this into SingleOperandInstruction ?
        assert isinstance(instruction, SingleOperandInstruction)

        access_sizes = {
            OperandWidth.BYTE: 1,
            OperandWidth.WORD: 2,
        }
        width = access_sizes[instruction.width]

        if instruction.addressing_mode == AddressingMode.DIRECT:
            if instruction.width == OperandWidth.WORD:
                val = state.cpu.registers[instruction.register]

            elif instruction.width == OperandWidth.BYTE:
                val = Extract(7, 0, state.cpu.registers[instruction.register])

        elif instruction.addressing_mode == AddressingMode.INDEXED:
            address = state.cpu.registers[instruction.register] + \
                    instruction.operand
            if instruction.width == OperandWidth.WORD:
                val = \
                        Concat(state.memory[address + 1], \
                        state.memory[address])

            elif instruction.width == OperandWidth.BYTE:
                val = state.memory[address]

        elif instruction.addressing_mode == AddressingMode.INDIRECT:
            address = state.cpu.registers[instruction.register]
            if instruction.width == OperandWidth.WORD:
                val = \
                        Concat(state.memory[address + 1], \
                        state.memory[address])

            elif instruction.width == OperandWidth.BYTE:
                val = state.memory[address]

        elif instruction.addressing_mode == AddressingMode.AUTOINCREMENT:
            address = state.cpu.registers[instruction.register]
            if instruction.width == OperandWidth.WORD:
                val = \
                        Concat(state.memory[address + 1], \
                        state.memory[address])

            elif instruction.width == OperandWidth.BYTE:
                val = state.memory[address]

            state.cpu.registers[instruction.register] += width
            
        elif instruction.addressing_mode == AddressingMode.SYMBOLIC:
            address = \
                    instruction.operand + state.cpu.registers[Register.R0]
            if instruction.width == OperandWidth.WORD:
                val = \
                        Concat(state.memory[address + 1], \
                        state.memory[address])

            elif instruction.width == OperandWidth.BYTE:
                val = state.memory[address]

        elif instruction.addressing_mode == AddressingMode.IMMEDIATE:
            if instruction.width == OperandWidth.WORD:
                val = instruction.operand 
            elif instruction.width == OperandWidth.BYTE:
                # I'm 99% sure SLAU144J 4.4.7.1 implies we mask off low byte
                # That also makes sense semantically, so we do that
                val = Extract(7, 0, instruction.operand)

        elif instruction.addressing_mode == AddressingMode.ABSOLUTE:
            address = instruction.operand
            if instruction.width == OperandWidth.WORD:
                val = \
                        Concat(state.memory[address + 1], \
                        state.memory[address])

            elif instruction.width == OperandWidth.BYTE:
                val = state.memory[address]

        elif instruction.addressing_mode == AddressingMode.CONSTANT4:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(4, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(4, 8)

        elif instruction.addressing_mode == AddressingMode.CONSTANT8:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(8, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(8, 8)

        elif instruction.addressing_mode == AddressingMode.CONSTANT0:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(0, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(0, 8)

        elif instruction.addressing_mode == AddressingMode.CONSTANT1:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(1, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(1, 8)

        elif instruction.addressing_mode == AddressingMode.CONSTANT2:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(2, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(2, 8)

        elif instruction.addressing_mode == AddressingMode.CONSTANTNEG1:
            if instruction.width == OperandWidth.WORD:
                val = BitVecVal(-1, 16)

            elif instruction.width == OperandWidth.BYTE:
                val = BitVecVal(-1, 8)

        return val

    def set_single_operand_value(self, state, instruction, value):
        """
        Get the operand value for a single-operand instruction

        NOTE: not pure!!! may modify a register if the addressing mode is
        AUTOINCREMENT
        """
        #XXX: Consider moving this into SingleOperandInstruction ?
        assert isinstance(instruction, SingleOperandInstruction)

        access_sizes = {
            OperandWidth.BYTE: 1,
            OperandWidth.WORD: 2,
        }
        width = access_sizes[instruction.width]

        if instruction.addressing_mode == AddressingMode.DIRECT:
            if instruction.width == OperandWidth.WORD:
                state.cpu.registers[instruction.register] = value

            elif instruction.width == OperandWidth.BYTE:
                high = Extract(15, 7, state.cpu.registers[instruction.register])
                state.cpu.registers[instruction.register] = Concat(high, value)

        elif instruction.addressing_mode == AddressingMode.INDEXED:
            address = state.cpu.registers[instruction.register] + \
                    instruction.operand
            if instruction.width == OperandWidth.WORD:
                high = Extract(15, 7, value)
                low = Extract(7, 0, value)
                state.memory[address] = low
                state.memory[address+1] = high

            elif instruction.width == OperandWidth.BYTE:
                state.memory[address] = value

        elif instruction.addressing_mode == AddressingMode.INDIRECT:
            address = state.cpu.registers[instruction.register]
            if instruction.width == OperandWidth.WORD:
                high = Extract(15, 7, value)
                low = Extract(7, 0, value)
                state.memory[address] = low
                state.memory[address+1] = high

            elif instruction.width == OperandWidth.BYTE:
                state.memory[address] = value

        elif instruction.addressing_mode == AddressingMode.AUTOINCREMENT:
            address = state.cpu.registers[instruction.register]
            if instruction.width == OperandWidth.WORD:
                high = Extract(15, 7, value)
                low = Extract(7, 0, value)
                state.memory[address] = low
                state.memory[address+1] = high

            elif instruction.width == OperandWidth.BYTE:
                state.memory[address] = value
            
        elif instruction.addressing_mode == AddressingMode.SYMBOLIC:
            address = \
                    instruction.operand + state.cpu.registers[Register.R0]
            if instruction.width == OperandWidth.WORD:
                high = Extract(15, 7, value)
                low = Extract(7, 0, value)
                state.memory[address] = low
                state.memory[address+1] = high

            elif instruction.width == OperandWidth.BYTE:
                state.memory[address] = value

        elif instruction.addressing_mode == AddressingMode.IMMEDIATE:
            raise ValueError('Cannot set an immediate!')

        elif instruction.addressing_mode == AddressingMode.ABSOLUTE:
            address = instruction.operand
            if instruction.width == OperandWidth.WORD:
                high = Extract(15, 7, value)
                low = Extract(7, 0, value)
                state.memory[address] = low
                state.memory[address+1] = high

            elif instruction.width == OperandWidth.BYTE:
                state.memory[address] = value

        elif instruction.addressing_mode == AddressingMode.CONSTANT4:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

        elif instruction.addressing_mode == AddressingMode.CONSTANT8:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

        elif instruction.addressing_mode == AddressingMode.CONSTANT0:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

        elif instruction.addressing_mode == AddressingMode.CONSTANT1:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

        elif instruction.addressing_mode == AddressingMode.CONSTANT2:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

        elif instruction.addressing_mode == AddressingMode.CONSTANTNEG1:
            if instruction.width == OperandWidth.WORD:
                raise ValueError('Cannot set a constant!')

            elif instruction.width == OperandWidth.BYTE:
                raise ValueError('Cannot set a constant!')

    def get_double_operand_source_value(self, state, instruction):
        """
        Get the source value for a double-operand instruction

        NOTE: not pure!!! may modify a register if the addressing mode is
        AUTOINCREMENT
        """
        #XXX: Consider moving this into DoubleOperandInstruction ?
        assert isinstance(instruction, DoubleOperandInstruction)

        access_sizes = {
            OperandWidth.BYTE: 1,
            OperandWidth.WORD: 2,
        }
        width = access_sizes[instruction.width]

        if instruction.source_addressing_mode == AddressingMode.DIRECT:
            if instruction.width == OperandWidth.WORD:
                source_val = state.cpu.registers[instruction.source_register]

            elif instruction.width == OperandWidth.BYTE:
                source_val = Extract(7, 0, state.cpu.registers[instruction.source_register])

        elif instruction.source_addressing_mode == AddressingMode.INDEXED:
            source_address = state.cpu.registers[instruction.source_register] + \
                    instruction.source_operand
            if instruction.width == OperandWidth.WORD:
                source_val = \
                        Concat(state.memory[source_address + 1], \
                        state.memory[source_address])

            elif instruction.width == OperandWidth.BYTE:
                source_val = state.memory[source_address]

        elif instruction.source_addressing_mode == AddressingMode.INDIRECT:
            source_address = state.cpu.registers[instruction.source_register]
            if instruction.width == OperandWidth.WORD:
                source_val = \
                        Concat(state.memory[source_address + 1], \
                        state.memory[source_address])

            elif instruction.width == OperandWidth.BYTE:
                source_val = state.memory[source_address]

        elif instruction.source_addressing_mode == AddressingMode.AUTOINCREMENT:
            source_address = state.cpu.registers[instruction.source_register]
            if instruction.width == OperandWidth.WORD:
                source_val = \
                        Concat(state.memory[source_address + 1], \
                        state.memory[source_address])

            elif instruction.width == OperandWidth.BYTE:
                source_val = state.memory[source_address]

            state.cpu.registers[instruction.source_register] += width
            
        elif instruction.source_addressing_mode == AddressingMode.SYMBOLIC:
            source_address = \
                    instruction.source_operand + state.cpu.registers[Register.R0]
            if instruction.width == OperandWidth.WORD:
                source_val = \
                        Concat(state.memory[source_address + 1], \
                        state.memory[source_address])

            elif instruction.width == OperandWidth.BYTE:
                source_val = state.memory[source_address]

        elif instruction.source_addressing_mode == AddressingMode.IMMEDIATE:
            if instruction.width == OperandWidth.WORD:
                source_val = instruction.source_operand 
            elif instruction.width == OperandWidth.BYTE:
                # I'm 99% sure SLAU144J 4.4.7.1 implies we mask off low byte
                # That also makes sense semantically, so we do that
                source_val = Extract(7, 0, instruction.source_operand)

        elif instruction.source_addressing_mode == AddressingMode.ABSOLUTE:
            source_address = instruction.source_operand
            if instruction.width == OperandWidth.WORD:
                source_val = \
                        Concat(state.memory[source_address + 1], \
                        state.memory[source_address])

            elif instruction.width == OperandWidth.BYTE:
                source_val = state.memory[source_address]

        elif instruction.source_addressing_mode == AddressingMode.CONSTANT4:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(4, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(4, 8)

        elif instruction.source_addressing_mode == AddressingMode.CONSTANT8:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(8, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(8, 8)

        elif instruction.source_addressing_mode == AddressingMode.CONSTANT0:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(0, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(0, 8)

        elif instruction.source_addressing_mode == AddressingMode.CONSTANT1:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(1, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(1, 8)

        elif instruction.source_addressing_mode == AddressingMode.CONSTANT2:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(2, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(2, 8)

        elif instruction.source_addressing_mode == AddressingMode.CONSTANTNEG1:
            if instruction.width == OperandWidth.WORD:
                source_val = BitVecVal(-1, 16)

            elif instruction.width == OperandWidth.BYTE:
                source_val = BitVecVal(-1, 8)

        return source_val

    def get_double_operand_dest_location(self, state, instruction):
        """
        Get the source location, and the type of access for a double-operand
        instruction.

        Returns a tuple (location, DestinationType)
        """
        if instruction.dest_addressing_mode == AddressingMode.DIRECT:
            dest_loc = instruction.dest_register
            dest_type = DestinationType.REGISTER

        elif instruction.dest_addressing_mode == AddressingMode.INDEXED:
            dest_loc = state.cpu.registers[instruction.dest_register] + \
                    instruction.dest_operand
            dest_type = DestinationType.ADDRESS

        elif instruction.dest_addressing_mode == AddressingMode.SYMBOLIC:
            dest_loc = state.cpu.registers[Register.R0] + instruction.dest_operand
            dest_type = DestinationType.ADDRESS

        elif instruction.dest_addressing_mode == AddressingMode.ABSOLUTE:
            dest_loc = instruction.dest_operand
            dest_type = DestinationType.ADDRESS

        return dest_loc, dest_type

    def step_rrc(self, state, instruction):
        assert instruction.opcode == Opcode.RRC
        raise NotImplementedError('rrc instruction')

    def step_swpb(self, state, instruction):
        assert instruction.opcode == Opcode.SWPB

        st = state.clone()

        value = self.get_single_operand_value(st, instruction)

        high = Extract(15, 8, value)
        low = Extract(7, 0, value)

        res = Concat(low, high)
        # put it back in the right place
        self.set_single_operand_value(st, instruction, res)

        return [st]

    def step_rra(self, state, instruction):
        assert instruction.opcode == Opcode.RRA
        raise NotImplementedError('rra instruction')

    def step_sxt(self, state, instruction):
        assert instruction.opcode == Opcode.SXT

        st = state.clone()

        value = self.get_single_operand_value(st, instruction)

        sign = Extract(7, 7, value)
        base = Extract(7, 0, value)
        extended_sign = Concat(*[sign]*8) # XXX: maybe implement as an If instead?
        extended_num = Concat(extended_sign, base)

        # Flags:
        # N: Set if ext < 0, reset otherwise
        # Z: set if ext = 0, reset otherwise
        # C: set if ext != 0, reset otherwise
        # V: reset
        new_states = [st]
        
        # N flag
        set_states = [x for x in new_states]
        unset_states = [x.clone() for x in new_states]
        for st in set_states:
            st.path.add(extended_num < 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_N, 16)
        for st in unset_states:
            st.path.add(extended_num >= 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_N, 16)
        new_states = set_states + unset_states

        # Z + C flags
        set_states = [x for x in new_states] # states where Z is set (C unset)
        unset_states = [x.clone() for x in new_states] # states where Z is unset (C set)
        for st in set_states:
            st.path.add(extended_num == 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_C, 16)
        for st in unset_states:
            st.path.add(extended_num != 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_C, 16)
        new_states = set_states + unset_states

        # V flag
        # all unset
        for st in new_states:
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_V, 16)

        return new_states

    def step_push(self, state, instruction):
        assert instruction.opcode == Opcode.PUSH

        st = state.clone()

        target = self.get_single_operand_value(st, instruction)
        self.push(st, target)

        return [st]

    def step_call(self, state, instruction):
        assert instruction.opcode == Opcode.CALL

        target = self.get_single_operand_value(state, instruction)
        
        if target == self.interrupt_address: # callgated addr for interrupts
            # interrupt number in high-byte of R2
            # LockIt manual appears to be incomplete, top bit is always 1, so
            # we ignore that
            interrupt_number = Extract(14, 8, state.cpu.registers[Register.R2])
            # TODO: what if this is symbolic?
            interrupt_number = simplify(interrupt_number).as_long()
            interrupt_fn = self.interrupts[interrupt_number]
            return interrupt_fn(state)

        st = state.clone()
        self.push(st, st.cpu.registers[Register.R0])
        st.cpu.registers[Register.R0] = target

        return [st]

    def step_reti(self, state, instruction):
        assert instruction.opcode == Opcode.RETI
        raise NotImplementedError('reti instruction')

    def step_jnz(self, state, instruction):
        assert instruction.opcode == Opcode.JNZ

        taken = state.clone()
        not_taken = state.clone()
        
        taken.path.add(taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_Z, 16) == 0)
        taken.cpu.registers[Register.R0] = instruction.target

        not_taken.path.add(not_taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_Z, 16) == self.registers.mask_Z)
        # R0 is already pointing at the next instruction

        return [taken, not_taken]

    def step_jz(self, state, instruction):
        assert instruction.opcode == Opcode.JZ

        taken = state.clone()
        not_taken = state.clone()
        
        taken.path.add(taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_Z, 16) == self.registers.mask_Z)
        taken.cpu.registers[Register.R0] = instruction.target

        not_taken.path.add(not_taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_Z, 16) == 0)
        # R0 is already pointing at the next instruction

        return [taken, not_taken]

    def step_jnc(self, state, instruction):
        assert instruction.opcode == Opcode.JNC
        raise NotImplementedError('jnc instruction')

    def step_jc(self, state, instruction):
        assert instruction.opcode == Opcode.JC

        taken = state.clone()
        not_taken = state.clone()
        
        taken.path.add(taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_C, 16) == self.registers.mask_C)
        taken.cpu.registers[Register.R0] = instruction.target

        not_taken.path.add(not_taken.cpu.registers[Register.R2] & BitVecVal(self.registers.mask_C, 16) == 0)
	# R0 is already pointing at the next instruction

        return [taken, not_taken]

    def step_jn(self, state, instruction):
        assert instruction.opcode == Opcode.JN
        raise NotImplementedError('jn instruction')

    def step_jge(self, state, instruction):
        assert instruction.opcode == Opcode.JGE
        raise NotImplementedError('jge instruction')

    def step_jl(self, state, instruction):
        assert instruction.opcode == Opcode.JL
        raise NotImplementedError('jl instruction')

    def step_jmp(self, state, instruction):
        assert instruction.opcode == Opcode.JMP

        st = state.clone()

        st.cpu.registers[Register.R0] = instruction.target
        
        return [st]

    def step_mov(self, state, instruction):
        """
        MOV instruction.

        Returns a list of successor states
        """
        assert instruction.opcode == Opcode.MOV

        st = state.clone() # our new state
        
        source_val = self.get_double_operand_source_value(st, instruction)

        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                st.cpu.registers[dest_loc] = source_val
            elif instruction.width == OperandWidth.BYTE:
                st.cpu.registers[dest_loc] = \
                        Concat(\
                        BitVecVal(0, 8), source_val)
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                st.memory[dest_loc] = Extract(7, 0, source_val)
                st.memory[dest_loc+1] = Extract(15, 8, source_val)
            elif instruction.width == OperandWidth.BYTE:
                st.memory[dest_loc] = source_val

        return [st]

    def step_add(self, state, instruction):
        assert instruction.opcode == Opcode.ADD

        st = state.clone()

        source_val = self.get_double_operand_source_value(st, instruction)
        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                dest_val = st.cpu.registers[dest_loc]
            elif instruction.width == OperandWidth.BYTE:
                dest_val = Extract(7, 0, st.cpu.registers[dest_loc])
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                dest_val = Concat(st.memory[dest_loc+1], \
                        st.memory[dest_loc])
            elif instruction.width == OperandWidth.BYTE:
                dest_val = st.memory[dest_loc]


        # From SLAU144J, the way all the flags are set:
        # N: Set if src + dest < 0, reset otherwise
        # Z: Set if src + dest = 0, reset otherwise
        # C: Set if there is a carry from MSB of result, reset otherwise
        # V: Set if overflow occurred, or:
        #       src > 0 and dest > 0 and src + dest < 0 OR
        #       src < 0 and dest < 0 and src + dest > 0,
        #       reset otherwise
        new_states = [st]

        # N bit
        set_states = [x for x in new_states] # N bit set
        unset_states = [x.clone() for x in new_states] # N bit cleared
        for st in set_states:
            st.path.add(source_val + dest_val < 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_N, 16)
        for st in unset_states:
            st.path.add(source_val + dest_val >= 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_N, 16)
        new_states = set_states + unset_states

        # Z bit
        set_states = [x for x in new_states] # N bit set
        unset_states = [x.clone() for x in new_states] # N bit cleared
        for st in set_states:
            st.path.add(source_val + dest_val == 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
        for st in unset_states:
            st.path.add(source_val + dest_val != 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
        new_states = set_states + unset_states

        # C bit
        # basically we check if the highest bit transitioned from a 1 to a 0
        highest_bit = lambda x: Extract(x.size()-1, x.size()-1, x)
        did_overflow = And(highest_bit(dest_val) == 1, \
                           highest_bit(dest_val - source_val) == 0)
        set_states = [x for x in new_states] # C bit set
        unset_states = [x.clone() for x in new_states] # C bit cleared
        for st in set_states:
            st.path.add(did_overflow)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_C, 16)
        for st in unset_states:
            st.path.add(Not(did_overflow))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_C, 16)
        new_states = set_states + unset_states

        # V bit
        # implemented as in the table above...
        set_states = [x for x in new_states] # N bit set
        unset_states = [x.clone() for x in new_states] # N bit cleared
        for st in set_states:
            cond_a = And(source_val > 0, dest_val > 0, source_val + dest_val < 0)
            cond_b = And(source_val < 0, dest_val < 0, source_val + dest_val > 0)
            st.path.add(Or(cond_a, cond_b))
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_V, 16)
        for st in unset_states:
            cond_a = And(source_val > 0, dest_val > 0, source_val + dest_val < 0)
            cond_b = And(source_val < 0, dest_val < 0, source_val + dest_val > 0)
            st.path.add(Not(Or(cond_a, cond_b)))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_V, 16)
        new_states = set_states + unset_states

        # set dest location to the sum in all states
        for st in new_states:
            if dest_type == DestinationType.REGISTER:
                if instruction.width == OperandWidth.WORD:
                    st.cpu.registers[dest_loc] = source_val + dest_val

                elif instruction.width == OperandWidth.BYTE:
                    # top bits get cloeared
                    st.cpu.registers[dest_loc] = Concat( \
                            BitVecVal(0, 8), \
                            source_val + dest_val)

            elif dest_type == DestinationType.ADDRESS:
                if instruction.width == OperandWidth.WORD:
                    st.memory[dest_loc] |= Extract(7, 0, source_val + dest_val)
                    st.memory[dest_loc+1] |= Extract(15, 8, source_val + dest_val)

                elif instruction.width == OperandWidth.BYTE:
                    st.memory[dest_loc] = source_val + dest_val

        return new_states

    def step_addc(self, state, instruction):
        assert instruction.opcode == Opcode.ADDC
        raise NotImplementedError('addc instruction')

    def step_subc(self, state, instruction):
        assert instruction.opcode == Opcode.SUBC
        raise NotImplementedError('subc instruction')

    def step_sub(self, state, instruction):
        assert instruction.opcode == Opcode.SUB
        st = state.clone()

        source_val = self.get_double_operand_source_value(st, instruction)
        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                dest_val = st.cpu.registers[dest_loc]
            elif instruction.width == OperandWidth.BYTE:
                dest_val = Extract(7, 0, st.cpu.registers[dest_loc])
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                dest_val = Concat(st.memory[dest_loc+1], \
                        st.memory[dest_loc])
            elif instruction.width == OperandWidth.BYTE:
                dest_val = st.memory[dest_loc]


        # From SLAU144J, the way all the flags are set:
        # N: Set if src > dest, reset if src <= dest
        # Z: Set if src = dest, reset if src != dest
        # C: Set if there is a carry from MSB, reset otherwise
        # V: Set if overflow occurs, reset otherwise, (more specifically, set if either:
        #       (src < 0 and dest > 0 and dest - src < 0) or
        #       (src > 0 and dest < 0 and dest - src > 0), unset otherwise)
        new_states = [st]

        # N bit
        set_states = [x for x in new_states] # N bit set
        unset_states = [x.clone() for x in new_states] # N bit cleared
        for st in set_states:
            st.path.add(source_val > dest_val)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_N, 16)
        for st in unset_states:
            st.path.add(source_val <= dest_val)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_N, 16)
        new_states = set_states + unset_states

        # Z bit
        set_states = [x for x in new_states] # Z bit set
        unset_states = [x.clone() for x in new_states] # Z bit cleared
        for st in set_states:
            st.path.add(source_val == dest_val)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
        for st in unset_states:
            st.path.add(source_val != dest_val)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
        new_states = set_states + unset_states


        # C bit
        # basically we check if the highest bit transitioned from a 1 to a 0
        highest_bit = lambda x: Extract(x.size()-1, x.size()-1, x)
        did_overflow = And(highest_bit(dest_val) == 1, \
                           highest_bit(dest_val - source_val) == 0)
        set_states = [x for x in new_states] # C bit set
        unset_states = [x.clone() for x in new_states] # C bit cleared
        for st in set_states:
            st.path.add(did_overflow)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_C, 16)
        for st in unset_states:
            st.path.add(Not(did_overflow))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_C, 16)
        new_states = set_states + unset_states
        
        # V bit
        set_states = [x for x in new_states] # V bit set
        unset_states = [x.clone() for x in new_states] # V bit cleared
        for st in set_states:
            # following conditions above...
            condA = And(source_val < 0, dest_val > 0, dest_val < source_val)
            condB = And(source_val > 0, dest_val < 0, dest_val > source_val)
            st.path.add(Or(condA, condB))
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_V, 16)
        for st in unset_states:
            # following conditions above...
            condA = And(source_val < 0, dest_val > 0, dest_val < source_val)
            condB = And(source_val > 0, dest_val < 0, dest_val > source_val)
            st.path.add(Not(Or(condA, condB)))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_V, 16)
        new_states = set_states + unset_states

        # set dest location to the difference in all states
        for st in new_states:
            if dest_type == DestinationType.REGISTER:
                if instruction.width == OperandWidth.WORD:
                    st.cpu.registers[dest_loc] = dest_val - source_val

                elif instruction.width == OperandWidth.BYTE:
                    # top bits get cloeared
                    st.cpu.registers[dest_loc] = Concat( \
                            BitVecVal(0, 8), \
                            dest_val - source_val)

            elif dest_type == DestinationType.ADDRESS:
                if instruction.width == OperandWidth.WORD:
                    st.memory[dest_loc] |= Extract(7, 0, dest_val - source_val)
                    st.memory[dest_loc+1] |= Extract(15, 8, dest_val - source_val)

                elif instruction.width == OperandWidth.BYTE:
                    st.memory[dest_loc] = dest_val - source_val

        return new_states

    def step_cmp(self, state, instruction):
        assert instruction.opcode == Opcode.CMP

        st = state.clone()

        source_val = self.get_double_operand_source_value(st, instruction)
        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                dest_val = st.cpu.registers[dest_loc]
            elif instruction.width == OperandWidth.BYTE:
                dest_val = Extract(7, 0, st.cpu.registers[dest_loc])
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                dest_val = Concat(st.memory[dest_loc+1], \
                        st.memory[dest_loc])
            elif instruction.width == OperandWidth.BYTE:
                dest_val = st.memory[dest_loc]


        # From SLAU144J, the way all the flags are set:
        # N: Set if src > dest, reset if src <= dest
        # Z: Set if src = dest, reset if src != dest
        # C: Set if there is a carry from MSB, reset otherwise
        # V: Set if overflow occurs, reset otherwise, (more specifically, set if either:
        #       (src < 0 and dest > 0 and dest - src < 0) or
        #       (src > 0 and dest < 0 and dest - src > 0), unset otherwise)
        new_states = [st]

        # N bit
        set_states = [x for x in new_states] # N bit set
        unset_states = [x.clone() for x in new_states] # N bit cleared
        for st in set_states:
            st.path.add(source_val > dest_val)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_N, 16)
        for st in unset_states:
            st.path.add(source_val <= dest_val)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_N, 16)
        new_states = set_states + unset_states

        # Z bit
        set_states = [x for x in new_states] # Z bit set
        unset_states = [x.clone() for x in new_states] # Z bit cleared
        for st in set_states:
            st.path.add(source_val == dest_val)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
        for st in unset_states:
            st.path.add(source_val != dest_val)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
        new_states = set_states + unset_states


        # C bit
        # basically we check if the highest bit transitioned from a 1 to a 0
        highest_bit = lambda x: Extract(x.size()-1, x.size()-1, x)
        did_overflow = And(highest_bit(dest_val) == 1, \
                           highest_bit(dest_val - source_val) == 0)
        set_states = [x for x in new_states] # C bit set
        unset_states = [x.clone() for x in new_states] # C bit cleared
        for st in set_states:
            st.path.add(did_overflow)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_C, 16)
        for st in unset_states:
            st.path.add(Not(did_overflow))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_C, 16)
        new_states = set_states + unset_states
        
        # V bit
        set_states = [x for x in new_states] # V bit set
        unset_states = [x.clone() for x in new_states] # V bit cleared
        for st in set_states:
            # following conditions above...
            condA = And(source_val < 0, dest_val > 0, dest_val < source_val)
            condB = And(source_val > 0, dest_val < 0, dest_val > source_val)
            st.path.add(Or(condA, condB))
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_V, 16)
        for st in unset_states:
            # following conditions above...
            condA = And(source_val < 0, dest_val > 0, dest_val < source_val)
            condB = And(source_val > 0, dest_val < 0, dest_val > source_val)
            st.path.add(Not(Or(condA, condB)))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_V, 16)
        new_states = set_states + unset_states

        return new_states

    def step_dadd(self, state, instruction):
        assert instruction.opcode == Opcode.DADD
        raise NotImplementedError('dadd instruction')

    def step_bit(self, state, instruction):
        assert instruction.opcode == Opcode.BIT
        st = state.clone() # our new state
        
        source_val = self.get_double_operand_source_value(st, instruction)

        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                dest_val = st.cpu.registers[dest_loc]
            elif instruction.width == OperandWidth.BYTE:
                dest_val = Extract(7, 0, st.cpu.registers[dest_loc])
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                dest_val = Concat(st.memory[dest_loc+1], \
                        st.memory[dest_loc])
            elif instruction.width == OperandWidth.BYTE:
                dest_val = st.memory[dest_loc]

        # Flag Semantics from SLAU144J:
        # N: Set if MSB of result is set, reset otherwise
        # Z: Set if result is zero, reset otherwise
        # C: Set if result is not zero, reset otherwise (.NOT. Zero)
        # V: Reset
        new_states = [st]

        # N flag
        set_states = [x for x in new_states]
        unset_states = [x.clone() for x in new_states]
        high_set = lambda x: Extract(x.size()-1, x.size()-1, x) == 0b1
        for state in set_states:
            state.path.add(high_set(source_val & dest_val))
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_N, 16)
        for state in unset_states:
            state.path.add(Not(high_set(source_val & dest_val)))
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_N, 16)
        new_states = set_states + unset_states

        # Z flag
        set_states = [x for x in new_states]
        unset_states = [x.clone() for x in new_states]
        for state in set_states:
            state.path.add((source_val & dest_val) == 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
        for state in unset_states:
            state.path.add((source_val & dest_val) != 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
        new_states = set_states + unset_states

        # C flag
        set_states = [x for x in new_states]
        unset_states = [x.clone() for x in new_states]
        for state in set_states:
            state.path.add((source_val & dest_val) != 0)
            st.cpu.registers[Register.R2] |= BitVecVal(self.registers.mask_Z, 16)
        for state in unset_states:
            state.path.add((source_val & dest_val) == 0)
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_Z, 16)
        new_states = set_states + unset_states

        # V flag
        for state in new_states:
            st.cpu.registers[Register.R2] &= ~BitVecVal(self.registers.mask_V, 16)

        return new_states

    def step_bic(self, state, instruction):
        assert instruction.opcode == Opcode.BIC

        st = state.clone() # our new state
        
        source_val = self.get_double_operand_source_value(st, instruction)

        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                st.cpu.registers[dest_loc] &= ~source_val
            elif instruction.width == OperandWidth.BYTE:
                st.cpu.registers[dest_loc] &= \
                        ~Concat( \
                        BitVecVal(0, 8), source_val)
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                st.memory[dest_loc] &= ~Extract(7, 0, source_val)
                st.memory[dest_loc+1] &= ~Extract(15, 8, source_val)
            elif instruction.width == OperandWidth.BYTE:
                st.memory[dest_loc] &= ~source_val

        return [st]

    def step_bis(self, state, instruction):
        assert instruction.opcode == Opcode.BIS

        st = state.clone() # our new state
        
        source_val = self.get_double_operand_source_value(st, instruction)

        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                st.cpu.registers[dest_loc] |= source_val
            elif instruction.width == OperandWidth.BYTE:
                st.cpu.registers[dest_loc] |= \
                        Concat( \
                        BitVecVal(0, 8), source_val)
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                st.memory[dest_loc] |= Extract(7, 0, source_val)
                st.memory[dest_loc+1] |= Extract(15, 8, source_val)
            elif instruction.width == OperandWidth.BYTE:
                st.memory[dest_loc] |= source_val

        return [st]

    def step_xor(self, state, instruction):
        assert instruction.opcode == Opcode.XOR
        raise NotImplementedError('xor instruction')

    def step_and(self, state, instruction):
        assert instruction.opcode == Opcode.AND

        st = state.clone() # our new state
        
        source_val = self.get_double_operand_source_value(st, instruction)

        dest_loc, dest_type = \
                self.get_double_operand_dest_location(st, instruction)

        #FIXME: Set status bits according to SLAU144J 3.4.6.4

        if dest_type == DestinationType.REGISTER:
            if instruction.width == OperandWidth.WORD:
                st.cpu.registers[dest_loc] &= source_val
            elif instruction.width == OperandWidth.BYTE:
                st.cpu.registers[dest_loc] &= \
                        Concat( \
                        BitVecVal(0, 8), source_val)
        elif dest_type == DestinationType.ADDRESS:
            if instruction.width == OperandWidth.WORD:
                st.memory[dest_loc] &= Extract(7, 0, source_val)
                st.memory[dest_loc+1] &= Extract(15, 8, source_val)
            elif instruction.width == OperandWidth.BYTE:
                st.memory[dest_loc] &= source_val

        return [st]

    def int_putchar(self, state):
        st = state.clone()

        ARG_OFFSET = 6 # how far up the stack is our arg

        out_address = st.cpu.registers[Register.R1] + ARG_OFFSET
        out_val = st.memory[out_address]

        st.sym_output.add(out_val)

        return [st]

    def int_getchar(self, state):
        raise NotImplementedError('getchar interrupt')

    def int_gets(self, state):
        st = state.clone()

        ARG_OFFSET = 6 # how far up the stack are our args

        r1 = st.cpu.registers[Register.R1]

        dest_low = st.memory[r1 + ARG_OFFSET]
        dest_high = st.memory[r1 + ARG_OFFSET + 1]

        dest_addr = Concat(dest_high, dest_low)
        
        length_low = st.memory[r1 + ARG_OFFSET + 2]
        length_high = st.memory[r1 + ARG_OFFSET + 3]

        length = Concat(length_high, length_low)

        sym_bytes = st.sym_input.generate_input(length)

        # write into memory
        for i, v in enumerate(sym_bytes):
            st.memory[dest_addr + i] = v

        # TODO: only do this if ALL the others are != 0
        all_nonzero = And([x != 0 for x in sym_bytes])
        # if all are nonzero, byte after last is set to zero
        st.memory[dest_addr + length + 1] = If(all_nonzero, \
                                               BitVecVal(0, 8), \
                                               st.memory[dest_addr + length + 1])

        return [st]

    def int_enabledep(self, state):
        raise NotImplementedError('enabledep interrupt')

    def int_setpageperms(self, state):
        raise NotImplementedError('setpageperms interrupt')

    def int_rand(self, state):
        raise NotImplementedError('rand interrupt')

    def int_hsm1check(self, state):
        st = state.clone()

        # XXX: We don't actually check this right now, just return as if
        # the answer was incorrect. Unless I run into a problem which has
        # an actual intended solution of guessing the HSM pass, this is
        # clearly never going to do anything.

        return [st]

    def int_hsm2check(self, state):
        st = state.clone()

        # XXX: We don't actually check this right now, just return as if
        # the answer was incorrect. Unless I run into a problem which has
        # an actual intended solution of guessing the HSM pass, this is
        # clearly never going to do anything.

        return [st]

    def int_unlock(self, state):
        st = state.clone()
        st.unlocked = True
        return [st]
