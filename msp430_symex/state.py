from copy import copy
import random
import z3

from .code import decode_instruction, Opcode, AddressingMode, Register
from .memory import Memory, parse_mc_memory_dump
from .cpu import CPU
from .symio import IO, IOKind

class Path:
    """
    The path predicate through the program.

    Call .add() to add a condition to the path

    Call .pred() to get a predicate suitable for Z3

    Call .clone() to get a copy-on-write version of the path
    """
    def __init__(self, paths=None):
        if paths is None:
            self._path = []
        else:
            self._path = paths
        self.__needs_copying = False
        self.model = None
        self._model_cache = {}
        self.sat = None # unknown

    def add(self, condition):
        """
        Add a condition to this path
        """
        if self.__needs_copying:
            self._path = copy(self._path)
            self.__needs_copying = False
        self._path.append(condition)
        self.model = None
        self.sat = None

    def make_unsat(self):
        """
        Helper function to make this state unsat
        """
        self.add(False)

    def pred(self):
        """
        Get the predicate for this path, suitable to throw at Z3
        """
        # Cache the predicate, as testing has found this gives
        # a 3-4x improvement to execution speed
        pred = z3.And(*self._path)
        # simplifying here makes things a bit (~5-10%) faster...
        # strange that Z3 doesn't do that internally
        pred = z3.simplify(pred)
        self._path = [pred]
        self.__needs_copying = False
        return pred

    def is_sat(self):
        # if we've cached whether we're sat, just return that
        if self.sat is not None:
            return self.sat
        # if we're in the global cache, use that
        if self.pred() in self._model_cache:
            self.sat, self.model = self._model_cache[self.pred()]
            return self.sat
        solver = z3.Solver()
        solver.add(self.pred())
        is_sat = solver.check() == z3.sat
        self.sat = is_sat
        if is_sat:
            self.model = solver.model()

        # Save sat results back to global cache
        self._model_cache[self.pred()] = (self.sat, self.model)

        return is_sat

    def clone(self):
        new_path = Path(self._path)
        new_path.__needs_copying = True
        self.__needs_copying = True
        # pass along our model so sat checks quick-exit as long as nothing is added
        new_path.model = self.model
        new_path.sat = self.sat

        new_path._model_cache = self._model_cache # NOT A COPY -- GLOBAL CACHE
        return new_path

    def __repr__(self):
        return 'Path({})'.format(self._path)


class State:
    """
    Entire encapsulation of the current state of the machine (register, memory),
    plus all the interrupts (and their associated summary functions)
    """
    def __init__(self, cpu, memory, path, sym_input, sym_output, unlocked, ticks=0):
        self.cpu = cpu
        self.memory = memory
        self.path = path
        self.sym_input = sym_input
        self.sym_output = sym_output
        self.unlocked = unlocked
        self.ticks = ticks

    def step(self, enable_unsound_optimizations=True):
        """
        Tick the cpu forward one instruction.

        Returns a list of successor states.
        """
        instruction_pointer = self.cpu.registers[Register.R0]
        if z3.is_bv(instruction_pointer):
            instruction_pointer = z3.simplify(instruction_pointer).as_long()
# pull enough to encode any instruction
        raw_instruction = \
                self.memory[instruction_pointer : instruction_pointer + 6]
        instruction, instruction_length = \
                decode_instruction(instruction_pointer, raw_instruction)
        #print(instruction, instruction_length)

        step_functions = {
            Opcode.RRC: self.cpu.step_rrc,
            Opcode.SWPB: self.cpu.step_swpb,
            Opcode.RRA: self.cpu.step_rra,
            Opcode.SXT: self.cpu.step_sxt,
            Opcode.PUSH: self.cpu.step_push,
            Opcode.CALL: self.cpu.step_call,
            Opcode.RETI: self.cpu.step_reti,
            Opcode.JNZ: self.cpu.step_jnz,
            Opcode.JZ: self.cpu.step_jz,
            Opcode.JNC: self.cpu.step_jnc,
            Opcode.JC: self.cpu.step_jc,
            Opcode.JN: self.cpu.step_jn,
            Opcode.JGE: self.cpu.step_jge,
            Opcode.JL: self.cpu.step_jl,
            Opcode.JMP: self.cpu.step_jmp,
            Opcode.MOV: self.cpu.step_mov,
            Opcode.ADD: self.cpu.step_add,
            Opcode.ADDC: self.cpu.step_addc,
            Opcode.SUBC: self.cpu.step_subc,
            Opcode.SUB: self.cpu.step_sub,
            Opcode.CMP: self.cpu.step_cmp,
            Opcode.DADD: self.cpu.step_dadd,
            Opcode.BIT: self.cpu.step_bit,
            Opcode.BIC: self.cpu.step_bic,
            Opcode.BIS: self.cpu.step_bis,
            Opcode.XOR: self.cpu.step_xor,
            Opcode.AND: self.cpu.step_and,
        }
        self.cpu.registers[Register.R0] += instruction_length # preincrement ip
        instruction_fn = step_functions[instruction.opcode]
        successor_states = instruction_fn(self, instruction, \
                enable_unsound_optimizations=enable_unsound_optimizations)
        return successor_states

    def clone(self):
         return self.__class__(self.cpu.clone(), self.memory.clone(), self.path.clone(), self.sym_input.clone(), self.sym_output.clone(), self.unlocked, self.ticks+1)

    def has_symbolic_ip(self):
        ip = self.cpu.registers[Register.R0]
        return z3.is_bv(ip) and not isinstance(z3.simplify(ip), z3.BitVecNumRef)

    def decode_some_instructions(self, ip, n):
        """
        Decodes **up to** :n: instructions, starting at :ip:

        Stops at ret instructions
        """

        # ret == mov @sp+, pc, so we have to do this huge thing
        is_ret = lambda insn: insn.opcode == Opcode.RETI or \
                (insn.opcode == Opcode.MOV and \
                insn.source_addressing_mode == AddressingMode.AUTOINCREMENT and \
                insn.source_register == Register.R1 and \
                insn.dest_register == Register.R0)

        instructions = []
        for _ in range(n):
            raw_instruction = self.memory[ip : ip + 6]
            instruction, instruction_length = \
                    decode_instruction(ip, raw_instruction)
            
            instructions.append(instruction)
            ip += instruction_length
            # stop analyzing on ret since we don't know what
            # could be past there (end of memory, random data)
            if is_ret(instruction):
                break
        return instructions


class PathGroup:
    def __init__(self, active, avoid=None):
        self.active = set(active)
        self.unlocked = set() # states with the lock unlocked
        self.unsat = set()
        self.symbolic = set() # paths with symbolic control data
        self.recently_added = set()
        self.tick_count = 0
        if isinstance(avoid, int):
            avoid = (avoid,) # wrap int avoid in a tuple
        self.avoid = avoid

    def prune(self):
        """
        Move any unsat states in this PathGroup that are in the active set to
        the unsat set
        """
        sat_states = set()
        symbolic_states = set()
        unlocked_states = set()
        unsat_states = set()
        for state in self.active:

            if state.path.is_sat():
                if state.has_symbolic_ip():
                    symbolic_states.add(state)

                if state.unlocked:
                    unlocked_states.add(state)
                else:
                    sat_states.add(state)
            else:
                #print('Marking state unsat:', state, state.path._path[-1])
                unsat_states.add(state)

        self.active = set(sat_states)
        self.unsat.update(unsat_states)
        self.unlocked.update(unlocked_states)
        self.symbolic.update(symbolic_states)

    def select_next_state(self):
        """
        Select the next state to simulate from the active group, removing it
        from that group
        """
        # TODO: more effective strategies?
        if len(self.active) > 64:
            choice = max(self.active, key=lambda st: st.ticks)
        else:
            choice = min(self.active, key=lambda st: st.ticks)
        self.active.discard(choice)
        return choice

    def step(self, enable_unsound_optimizations=True):
        path_to_sim = self.select_next_state()
        successors = set(path_to_sim.step(enable_unsound_optimizations=enable_unsound_optimizations))
        self.active.update(successors)
        self.recently_added = successors
        self.tick_count += 1

        for state in successors:
            # make states at an avoid_addr unsat
            # TODO: maybe check recent states?
            if self.avoid:
                def simplify(v):
                    if z3.is_bv(v):
                        v = z3.simplify(v).as_long()
                    return v
                try:
                    ip = simplify(state.cpu.registers[Register.R0])
                    if ip in self.avoid:
                        state.path.make_unsat()
                except AttributeError:
                    pass # symbolic ip!! Ignore for now...

        self.prune() # prune unsat successors

    def step_until_symbolic_ip(self, enable_unsound_optimizations=True, debug_print=False):
        while self.active and not self.symbolic:
            self.step(enable_unsound_optimizations=enable_unsound_optimizations)
            print('==== Steps: {} == Active: {} == Unsat: {} ===='.format(self.tick_count, len(self.active), len(self.unsat)))
            if debug_print:
                for state in self.active:
                    ip = state.cpu.registers['R0']
                    if z3.is_bv(ip):
                        ip = z3.simplify(ip).as_long()
                    print('\t', state)
                    print('\t\tIP:', hex(ip))
                    print('\t\tInput:', [x.rstrip(b'\xc0') for x in state.sym_input.dump(state)])
                    print('\t\tOutput:', repr(state.sym_output.dump(state)))


    def step_until_unlocked(self, enable_unsound_optimizations=True, debug_print=False):
        while self.active and not self.unlocked:
            self.step(enable_unsound_optimizations=enable_unsound_optimizations)
            print('==== Steps: {} == Active: {} == Unsat: {} ===='.format(self.tick_count, len(self.active), len(self.unsat)))
            if debug_print:
                for state in self.active:
                    ip = state.cpu.registers['R0']
                    if z3.is_bv(ip):
                        ip = z3.simplify(ip).as_long()
                    print('\t', state)
                    print('\t\tIP:', hex(ip))
                    print('\t\tInput:', repr(state.sym_input.dump(state).rstrip(b'\xc0')))
                    print('\t\tOutput:', repr(state.sym_output.dump(state)))



def start_path_group(memory_dump, start_ip, avoid=None):
    """
    Parse a memory dump, construct a base state, and return a PathGroup.
    """
    mem = parse_mc_memory_dump(memory_dump)
    cpu = CPU()
    cpu.registers[Register.R0] = z3.BitVecVal(start_ip, 16)
    path = Path()
    inp = IO(IOKind.INPUT, [])
    out = IO(IOKind.OUTPUT, [])


    entry_state = State(cpu, mem, path, inp, out, False)
    pg = PathGroup([entry_state], avoid=avoid)
    return pg

# shared instance of the backing memory so we don't need to keep building this
# make sure blank_state returns a clone of it's state so we don't accidentally
# reuse this instance!!
__memory_data = [z3.BitVecVal(0, 8) for _ in range(0xFFFF)]
def blank_state():
    cpu = CPU()
    memory = Memory(__memory_data)
    path = Path()
    inp = IO(IOKind.INPUT, [])
    out = IO(IOKind.OUTPUT, [])
    # return a clone because we cache __memory_data
    return State(cpu, memory, path, inp, out, False).clone()
