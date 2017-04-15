from z3 import simplify

from .code import Opcode, Register, AddressingMode, decode_instruction
from .state import State

def intval(val):
    """
    Turn the argument into an integer by any means neccesary
    unless you have to concretize symbolic data in which case go fuck yourself
    """
    if isinstance(val, int):
        return val

    val = simplify(val)
    val = val.as_long()
    return val

class CFG:
    
    def __init__(self, memory):
        self.memory = memory
        self.jump_opcodes = {Opcode.JNZ, Opcode.JZ, Opcode.JNC, Opcode.JC, \
                             Opcode.JN, Opcode.JGE, Opcode.JL, Opcode.JMP}
        self.conditional_jump_opcodes = self.jump_opcodes - {Opcode.JMP}
        self.undecodable_addresses = {0x10}

        self.functions = set()

    def generate_all_functions(self, program_entry_point):
        explored = set()
        frontier = {program_entry_point}
        while frontier:
            func_addr = frontier.pop()

            func, discovered_funcs = self.generate_function(func_addr)

            explored.add(func_addr)
            frontier.update(discovered_funcs - explored)

            self.functions.add(func)

    def generate_function(self, entry_point):
        called_addrs = set()
        boundaries = {entry_point}
        edges = set()
        frontier = {entry_point}
        explored = set()

        # Find basic-block boundries
        while frontier:

            found_jump = False
            ip = frontier.pop()
            explored.add(ip)

            # fast-fail on things like 0x10, the callgated interrupt address
            if ip in self.undecodable_addresses:
                continue

            while not found_jump:
                raw = self.memory[ip : ip + 6]
                insn, insn_len = decode_instruction(ip, raw)

                if insn.opcode == Opcode.CALL:
                    called = intval(insn.operand)
                    called_addrs.add((ip, called))

                # ret == mov @sp+, pc, so we have to do this huge thing
                is_ret = lambda insn: insn.opcode == Opcode.RETI or \
                            (insn.opcode == Opcode.MOV and \
                            insn.source_addressing_mode == AddressingMode.AUTOINCREMENT and \
                            insn.source_register == Register.R1 and \
                            insn.dest_register == Register.R0)
                if insn.opcode in self.jump_opcodes or is_ret(insn):
                    found_jump = True
                    if is_ret(insn):
                       succs = set() # no succs on ret
                    elif insn.opcode in self.conditional_jump_opcodes:
                        succs = {insn.target, ip + insn_len}
                    else:
                        succs = {insn.target}

                    succs = {intval(x) for x in succs}

                    frontier.update(succs - explored)
                    explored.add(ip)
                    edges.update({(ip, succ) for succ in succs})
                    boundaries.add(ip + insn_len) # add jmp-point
                    boundaries.update(succs)

                ip += insn_len

        # generate basic-blocks from boundaries
        boundaries = sorted(list(boundaries))
        bbs = []
        # BBs are [start_addr, end_addr)
        for start_addr, end_addr in zip(boundaries[:-1], boundaries[1:]):
            bb = BasicBlock(start_addr, end_addr)
            instructions = []
            ip = start_addr
            last_addr = start_addr
            # step up instructions to the one that *ends* at end_addr
            while ip != end_addr:
                raw = self.memory[ip : ip + 6]
                insn, insn_len = decode_instruction(ip, raw)
                instructions.append(insn)
                last_addr = ip
                ip += insn_len

            enters = {src for src, dst in edges if dst == start_addr}
            exits = {dst for src, dst in edges if src == last_addr}

            bb.instructions = instructions
            bb.incoming_edges = set(enters)
            bb.outgoing_edges = set(exits)

            bbs.append(bb)

        fn = Function(bbs)

        return fn, {addr for _, addr in called_addrs}


class Function:

    def __init__(self, basic_blocks):
        self.basic_blocks = basic_blocks


class BasicBlock:
    
    def __init__(self, start, end):
        self.start_address = start
        self.end_address = end
        self.instructions = []
        self.incoming_edges = set()
        self.outgoing_edges = set()

    def add_instruction(self, insn):
        if insn.address > self.end_address:
            self.end_address = insn.address

        self.instructions.append(insn)
