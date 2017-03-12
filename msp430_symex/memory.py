from copy import copy
from z3 import simplify, is_bv, BitVecVal, BitVecNumRef

from .code import Register

class Memory:
    """
    Represents memory.

    Bytes coming out of this might be BitVecs or numbers in [0, 255]

    Hopefully will implement a Copy-on-Write interface in the future,
    where memory is old references until it needs to be changed,
    at which point it copies off.
    """
    def __init__(self, data):
        """
        data is a list of values to initalize this memory with.
        Can be bytes or BitVecs of length 8.
        """
        self.data = data
        # Is data a reference to one out of another Memory?
        self.__needs_copying = False

    def clone(self):
        """
        Return a copy of this memory state

        NOTE: May not actually be a full copy, but a reference with
        copy-on-write flags set.
        """
        other = Memory(self.data)
        other.__needs_copying = True
        self.__needs_copying = True

        return other

    def _concretize(self, value):
        if isinstance(value, slice):
            # for now, just concretize each of the values
            # We could probably get a lot of milage out of doing a search on
            # all of these values together, but this should be enough for a
            # while
            start = self._concretize(value.start)
            stop = self._concretize(value.stop)
            step = self._concretize(value.step)
            value = slice(start, stop, step)
        if is_bv(value): # try to simplify and deal with BV's that come in...
            value = simplify(value)
            if isinstance(value, BitVecNumRef):
                value = value.as_long() # if this succeeds, we had a single value! yay
            else:
                # symbolic accesses are hard!!
                # TODO: deal with symbolic values
                raise ValueError('UH OH, THAT WAS A SYMBOLIC VARIABLE YOU TRIED TO INDEX MEMORY WITH D:')

        return value


    def __getitem__(self, key):
        key = self._concretize(key)
        return self.data[key]

    def __setitem__(self, key, value):
        if self.__needs_copying:
            self.data = copy(self.data)
            self.__needs_copying = False
        key = self._concretize(key)
        self.data[key] = value


def parse_mc_memory_dump(dump):
    """
    Pares a microcorruption memory dump, returns a Memory with that data
    """
    memory = [0 for _ in range(0, 0xffff+1)] # memory, initialized to 0's
    lines = dump.split('\n')
    for line in lines:
        line = line.strip()
        line_address = int(line[0:4], 16)
        data = line.split()[1:9]
        if data[0] == '*':
            continue # this line is unset (so 0's)
        else:
            data = ''.join(data)
            d = bytes.fromhex(data)
            for i,b in enumerate(d):
                memory[line_address + i] = b

    # BVVs for all the values in memory
    return Memory([BitVecVal(x, 8) for x in memory])
