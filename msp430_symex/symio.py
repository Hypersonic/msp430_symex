from copy import copy

from z3 import BitVec, simplify, is_bv, BitVecNumRef


class IO:
    def __init__(self, data):
        self.data = data
        self.__needs_copying = False
    
    def add(self, value):
        """
        Add a byte of data to the end of this stream.
        """
        if self.__needs_copying:
            self.data = copy(self.data)
            self.__needs_copying = False
        self.data.append(value)

    def dump(self, state):
        out = []
        if not state.path.is_sat():
            raise ValueError('path being dumped was unsat')
        model = state.path.model
        for x in self.data:
            x = simplify(x)
            try:
                x = x.as_long()
                x = bytes([x])
            except:
                x = model[x]
                if x is not None:
                    x = x.as_long()
                    x = bytes([x])
                else:
                    x = b'\xc0' # placeholder value for unconstrained
            out.append(x)
        return bytes().join(out)

    def generate_input(self, length):
        """
        Generate :length: bytes of symbolic data, add it to this, and return the bytes
        """

        length = self._concretize(length)

        new_bytes = []
        for _ in range(length):
            val = BitVec('inp_{}'.format(len(self.data)), 8)
            self.add(val)
            new_bytes.append(val)

        return new_bytes

    def clone(self):
        new_io = self.__class__(self.data)
        new_io.__needs_copying = True
        self.__needs_copying = True

        return new_io

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
