# up to 2^16 of 8-bit values
class Stack:
    def __init__(self):
        self.data = [0] * 0x10000  # addresses from 0x0000 to 0xFFFF
        self.sp = 0xFFFE
        self.tos = 0x00

    def get_next(self):
        # not exactly next, but returns value from stack by SP
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

    def write_tos_to_sp(self):
        self.data[self.sp] = self.tos

    def print_stack(self):
        if self.sp < 0xFFFD:
            for address in range(self.sp + 1):
                decimal_representation = self.data[address] if self.data[address] < 128 else self.data[address] - 256
                print(f"0x{address:04X} | 0x{self.data[address]:02X}  ==  {decimal_representation}", end="")
                if self.sp == address:
                    print(" <--")
                else:
                    print()
        print('-------------')
        decimal_representation = self.tos if self.tos < 128 else self.tos - 256
        print(f" TOS   | 0x{self.tos:02X}  ==  {decimal_representation}")
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

        self.ticks = 0

    def tick(self):
        self.ticks += 1

    def add(self):
        """
        tos + stack[sp] => tos; sp--
        """
        self.stack.tos = self.stack.tos + self.stack.get_next()

        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.stack.sp_dec()

        self.tick()

    def sub(self):
        """
        tos - stack[sp] => tos; sp--
        """
        self.stack.tos = self.stack.get_next() - self.stack.tos

        if self.stack.tos < 0:
            self.stack.tos += 0x100

        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False
        self.of = False  # Reset overflow flag for subtraction

        self.stack.sp_dec()

        self.tick()

    def mul(self):
        """
        tos * stack[sp] => tos; sp--
        """
        result_unsigned = self.stack.tos * self.stack.get_next()

        # If either operand is negative, adjust the result
        if (self.stack.tos & 0x80) != 0 and (self.stack.get_next() & 0x80) != 0:
            # Both operands are negative, result needs adjustment
            result_signed = -(0x100 - result_unsigned)
        elif (self.stack.tos & 0x80) != 0 or (self.stack.get_next() & 0x80) != 0:
            # One operand is negative, result needs adjustment
            result_signed = result_unsigned - 0x100
        else:
            # Both operands are positive, no adjustment needed
            result_signed = result_unsigned

        # Update TOS with the result
        self.stack.tos = result_signed & 0xFF

        # Set flags based on the result
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False
        self.of = True if result_signed > 0x7F or result_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def divide(self):
        """
        stack[sp] / tos => tos; sp--
        """
        divisor = self.stack.tos

        if divisor == 0:
            # Division by zero, handle error or set flags accordingly
            # For simplicity, let's set the result to 0 and flags to indicate an error
            self.stack.tos = 0
            self.zf = True
            self.nf = False
            self.of = True  # Indicate division by zero error
        else:
            # Perform division treating the numbers as signed integers
            quotient_signed = self.stack.get_next() // divisor

            # Update TOS with the quotient
            self.stack.tos = quotient_signed & 0xFF

            # Set flags based on the result
            self.zf = True if self.stack.tos == 0 else False
            self.nf = True if self.stack.tos >= 0x80 else False
            self.of = True if quotient_signed > 0x7F or quotient_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def mod(self):
        """
        stack[sp] % tos => tos; sp--
        """
        divisor = self.stack.tos

        if divisor == 0:
            # Division by zero, handle error or set flags accordingly
            # For simplicity, let's set the result to 0 and flags to indicate an error
            self.stack.tos = 0
            self.zf = True
            self.nf = False
            self.of = True  # Indicate division by zero error
        else:
            # Perform division treating the numbers as signed integers
            quotient_signed = self.stack.get_next() % divisor

            # Update TOS with the quotient
            self.stack.tos = quotient_signed & 0xFF

            # Set flags based on the result
            self.zf = True if self.stack.tos == 0 else False
            self.nf = True if self.stack.tos >= 0x80 else False
            self.of = True if quotient_signed > 0x7F or quotient_signed < -0x80 else False

        self.stack.sp_dec()

        self.tick()

    def over(self):
        self.stack.sp_inc()
        self.stack.data[self.stack.sp] = self.stack.tos
        self.stack.sp_dec()
        self.stack.tos = self.stack.data[self.stack.sp]
        self.stack.sp_inc()

    def drop(self):
        self.stack.tos = self.stack.data[self.stack.sp]
        self.stack.sp_dec()

    def swap(self):
        self.over()
        self.over()
        self.stack.sp_dec()
        self.stack.sp_dec()
        self.stack.write_tos_to_sp()
        self.stack.sp_inc()
        self.stack.sp_inc()
        self.stack.tos = self.stack.get_next()
        self.stack.sp_dec()
        self.stack.sp_dec()

    def inc(self):
        self.stack.tos += 1
        if self.stack.tos > 0xFF:
            self.stack.tos -= 0x100
            self.of = True
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick()

    def dec(self):
        self.stack.tos -= 1
        if self.stack.tos < 0:
            self.stack.tos += 0x100
        self.zf = True if self.stack.tos == 0 else False
        self.nf = True if self.stack.tos >= 0x80 else False

        self.tick()

    def dup(self):
        self.stack.sp_inc()
        self.stack.write_tos_to_sp()



if __name__ == '__main__':
    cu = ControlUnit()

    cu.stack.push(0x0a)
    cu.stack.push(0x0a)
    cu.stack.push(0x0a)
    cu.stack.push(0x0a)
    cu.stack.push(0x0b)

    cu.swap()

    cu.stack.print_stack()

    cu.over()
    cu.stack.print_stack()

    cu.swap()
    cu.stack.print_stack()

    # cu.stack.push(0xaa)
    # cu.stack.push(0xff)
    # cu.stack.push(0xcc)
    # cu.stack.push(0xdd)
    #
    # cu.stack.push(0x11)
    # cu.stack.push(0xff)
    # cu.stack.push(0x33)
    # cu.stack.push(0xff)
    #
    # cu.stack.sp = 0x0006
    #
    # cu.stack.sp -= 3
    # cu.sum()
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp += 3
    # cu.sum()
    # cu.stack.sp -= 4
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp += 3
    # cu.sum()
    # cu.stack.sp -= 4
    # cu.over()
    #
    # if cu.of:
    #     cu.stack.tos += 1
    #
    #     if cu.stack.tos != 0x00:
    #         cu.of = False
    #
    # cu.stack.sp += 3
    # cu.sum()
    # cu.stack.sp -= 4
    # cu.over()
    # cu.stack.sp += 3
    # cu.drop()
    # cu.stack.print_stack()
