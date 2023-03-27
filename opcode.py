import json


class Opcode:
    # address instructions
    PUSH = "PUSH"
    JMP = "JMP"
    JZ = "JZ"
    JNZ = "JNZ"

    # non-address instructions
    ADD = "ADD"
    SUB = "SUB"
    MOD = "MOD"

    DUP = "DUP"
    SWAP = "SWAP"
    DROP = "DROP"
    OVER = "OVER"
    SET = "SET"


def write_program(filename, program):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(program, indent=4))


def read_program(filename):
    """
    :param: имя файла, из которого читаем
    :return instructions - инструкции для занесения по адресам от 0x000 до 0x7FFF, data - переменные для
    последовательного занесения начиная с адреса 0x800
    """
    with open(filename, encoding="utf-8") as file:
        program = json.loads(file.read())
        return program["instructions"], program["data"]

