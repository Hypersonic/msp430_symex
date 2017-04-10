from enum import Enum
from copy import copy

from z3 import BitVec, simplify, is_bv, BitVecNumRef

class IOKind(Enum):
    INPUT = 0
    OUTPUT = 1


class IO:
    def __init__(self, kind, data):
        self.kind = kind
        self.data = data
        self.grouped_inputs = []
        self.__needs_copying = False
    
    def add(self, value):
        """
        Add a byte of data to the end of this stream.
        """
        self._resolve_copies()
        self.data.append(value)

    def dump(self, state):
        def get_byte(model, byte):
            """
            Resolve a symbolic byte into some concrete value
            """
            byte = simplify(byte)
            try:
                byte = byte.as_long()
                byte = bytes([byte])
            except:
                byte = model[byte]
                if byte is not None:
                    byte = byte.as_long()
                    byte = bytes([byte])
                else:
                    byte = b'\xc0' # placeholder value for unconstrained
            return byte

        if not state.path.is_sat():
            raise ValueError('path being dumped was unsat')
        model = state.path.model

        if self.kind == IOKind.INPUT:
            out = []
            for gi in self.grouped_inputs:
                gi_out = []
                for x in gi:
                    x = get_byte(model, x)
                    gi_out.append(x)

                out.append(bytes().join(gi_out))
            return out
        else:
            out = []
            for x in self.data:
                out.append(get_byte(model, x))
            return bytes().join(out)

    def generate_input(self, length):
        """
        Generate :length: bytes of symbolic data, add it to this, and return the bytes
        """

        self._resolve_copies()
        length = self._concretize(length)

        new_bytes = []
        for _ in range(length):
            val = BitVec('inp_{}'.format(len(self.data)), 8)
            self.add(val)
            new_bytes.append(val)

        self.grouped_inputs.append(new_bytes)
        return new_bytes

    def clone(self):
        new_io = self.__class__(self.kind, self.data)
        new_io.grouped_inputs = self.grouped_inputs
        new_io.__needs_copying = True
        self.__needs_copying = True

        return new_io
    
    def _resolve_copies(self):
        if self.__needs_copying:
            self.data = copy(self.data)
            self.grouped_inputs = copy(self.grouped_inputs)
            self.__needs_copying = False

    def _concretize(self, value):
        if is_bv(value): # try to simplify and deal with BV's that come in...
            value = simplify(value)
            if isinstance(value, BitVecNumRef):
                value = value.as_long() # if this succeeds, we had a single value! yay
            else:
                # symbolic lengths
                # TODO: deal with symbolic values
                raise ValueError('Tried to concretize symbolic data in an input... much danger, much scare, much fail!')

        return value
