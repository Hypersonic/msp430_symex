from copy import copy
import random
import z3

from .code import decode_instruction, Opcode, AddressingMode, Register
from .memory import Memory, parse_mc_memory_dump
from .cpu import CPU
from .symio import IO

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
        self._path = [pred]
        self.__needs_copying = False
        return pred

    def is_sat(self):
        # if we've cached whether we're sat, just return that
        if self.sat is not None:
            return self.sat
        solver = z3.Solver()
        solver.add(self.pred())
        is_sat = solver.check() == z3.sat
        self.sat = is_sat
        if is_sat:
            self.model = solver.model()
        return is_sat

    def clone(self):
        new_path = Path(self._path)
        new_path.__needs_copying = True
        self.__needs_copying = True
        # pass along our model so sat checks quick-exit as long as nothing is added
        new_path.model = self.model
        return new_path

    def __repr__(self):
        return 'Path({})'.format(self._path)


class State:
    """
    Entire encapsulation of the current state of the machine (register, memory),
    plus all the interrupts (and their associated summary functions)
    """
    def __init__(self, cpu, memory, path, sym_input, sym_output, unlocked):
        self.cpu = cpu
        self.memory = memory
        self.path = path
        self.sym_input = sym_input
        self.sym_output = sym_output
        self.unlocked = unlocked

    def step(self):
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
        successor_states = instruction_fn(self, instruction)
        return successor_states

    def clone(self):
         return self.__class__(self.cpu.clone(), self.memory.clone(), self.path.clone(), self.sym_input.clone(), self.sym_output.clone(), self.unlocked)

    def has_symbolic_ip(self):
        ip = self.cpu.registers[Register.R0]
        return z3.is_bv(ip) and not isinstance(z3.simplify(ip), z3.BitVecNumRef)


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
        # Perhaps prefer states which haven't been simulated in awhile?
        # we'd rather not pick recently added sets (we want to get some diversity)
        would_rather_not_select = self.recently_added
        if self.active - would_rather_not_select:
            # we have something we can choose that isn't in the recently
            # added set
            choice = random.choice(list(self.active - would_rather_not_select))
            self.active.discard(choice)
            return choice
        else:
            # we just have to pick anything off of the active set
            choice = random.choice(list(self.active))
            self.active.discard(choice)
            return choice

    def step(self):
        path_to_sim = self.select_next_state()
        successors = set(path_to_sim.step())
        self.active.update(successors)
        self.recently_added = successors
        self.tick_count += 1

        self.prune() # prune unsat successors

    def step_until_symbolic_ip(self):
        while self.active and not self.symbolic:
            self.step()
            print('==== Steps: {} == Active: {} == Unsat: {} ===='.format(self.tick_count, len(self.active), len(self.unsat)))
            for state in self.active:
                print('\t', state)
                print('\t\tInput:', repr(state.sym_input.dump(state).rstrip(b'\xc0')))
                print('\t\tOutput:', repr(state.sym_output.dump(state)))


    def step_until_unlocked(self):
        while self.active and not self.unlocked:
            self.step()
            print('==== Steps: {} == Active: {} == Unsat: {} ===='.format(self.tick_count, len(self.active), len(self.unsat)))
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
    inp = IO([])
    out = IO([])


    entry_state = State(cpu, mem, path, inp, out, False)
    pg = PathGroup([entry_state], avoid=avoid)
    return pg

def blank_state():
    # TODO: initialize stuff to sane non-None values
    cpu = CPU()
    memory_data = [z3.BitVecVal(0, 8) for _ in range(0xFFFF)]
    memory = Memory(memory_data)
    path = Path()
    inp = IO([])
    out = IO([])
    return State(cpu, memory, path, inp, out, False)
