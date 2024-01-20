# up to 2^16 of 8-bit values
class Stack:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.sp = 0xFFFE
        self.tos = 0x00

    def get_next(self):
        assert self.sp != 0xFFFE and self.sp != 0xFFFF, f'STACK ERROR: trying to get forbidden address (sp = {self.sp})'
        return self.data[self.sp]

    def get_tos(self):
        return self.tos

    def sp_inc(self):
        self.sp += 1

        if self.sp == (0xFFFF + 1):
            self.sp = 0x0000

    def sp_dec(self):
        self.sp -= 1

        if self.sp == -1:
            self.sp = 0xFFFF

    def push(self, value):
        self.sp_inc()
        self.data[self.sp] = self.tos
        assert -128 <= value <= 255, f'STACK: push filed with value {value}'
        self.tos = value

    def pop(self):
        self.tos = self.data[self.sp]
        self.sp_dec()

    def print_stack(self):
        for address in range(self.sp + 1):
            print(f"0x{address:04X} | {self.data[address]:02X}",end="")
            if self.sp == address:
                print(" <--")
            else:
                print()
        print('-------------')
        print(f" TOS   | {self.tos:02X}")
        print()


class RAM:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.ad = 0x0000

    def init_data(self, data):
        data_start = 0x0000
        for value in data:
            self.data[data_start] = value
            data_start += 1

    def latch_address(self, address):
        assert 0x0000 <= address <= 0xFFFF, f'RAM: address {hex(address)} out of bounds'
        self.ad = address

    def save(self, value):
        assert 0 <= value <= 255, "Attempt to put in RAM value that out of bounds"
        self.data[self.ad] = value

    def load(self):
        return self.data[self.ad]


class ControlUnit:
    def __init__(self):
        self.stack = Stack()

        self.of = False
        self.zf = False
        self.nf = False

    def sum(self):
        self.stack.tos = self.stack.tos + self.stack.get_next()

        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True

        self.stack.sp_dec()

    def over(self):
        self.stack.sp_inc()
        self.stack.data[self.stack.sp] = self.stack.tos
        self.stack.sp_dec()
        self.stack.tos = self.stack.data[self.stack.sp]
        self.stack.sp_inc()

    def drop(self):
        self.stack.tos = self.stack.data[self.stack.sp]
        self.stack.sp_dec()


if __name__ == '__main__':
    cu = ControlUnit()

    cu.stack.push(0xaa)
    cu.stack.push(0xff)
    cu.stack.push(0xcc)
    cu.stack.push(0xdd)

    cu.stack.push(0x11)
    cu.stack.push(0xff)
    cu.stack.push(0x33)
    cu.stack.push(0xff)

    cu.stack.sp = 0x0006



    cu.stack.sp -= 3
    cu.sum()
    cu.over()

    if cu.of:
        cu.stack.tos += 1

        if cu.stack.tos != 0x00:
            cu.of = False

    cu.stack.sp += 3
    cu.sum()
    cu.stack.sp -= 4
    cu.over()


    if cu.of:
        cu.stack.tos += 1

        if cu.stack.tos != 0x00:
            cu.of = False

    cu.stack.sp += 3
    cu.sum()
    cu.stack.sp -= 4
    cu.over()

    if cu.of:
        cu.stack.tos += 1

        if cu.stack.tos != 0x00:
            cu.of = False

    cu.stack.sp += 3
    cu.sum()
    cu.stack.sp -= 4
    cu.over()
    cu.stack.sp += 3
    cu.drop()
    cu.stack.print_stack()


