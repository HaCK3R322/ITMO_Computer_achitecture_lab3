# ITMO_Computer_achitecture_lab3
Translator + Proccessor

# Forth. Транслятор и модель

- Андросов Иван Сергеевич P33111.
- `forth | stack | harv | hw | tick | struct | stream | port | prob1`


## Язык программирования

``` ebnf
<program> ::= <statement>*
<statement> ::= <variable-declaration> | <conditional-statement> | <loop-statement> | <arithmetic-operation> | <stack-operation> | <io-operation> | <number>
<variable-declaration> ::= "VARIABLE" <identifier>
<conditional-statement> ::= "IF" <statement>* "THEN"
<loop-statement> ::= "BEGIN" <statement>* "UNTIL"
<arithmetic-operation> ::= "+" | "-" | "/" | "*" | "%" | "<" | ">" | "="
<stack-operation> ::= "@" | "!" | "SWAP" | "DROP" | "DUP" | "OVER"
<io-operation> ::= "." | "ACCEPT"
<identifier> ::= <letter> <letter-or-digit>*
<number> ::= <digit>+

<letter> ::= "a" | "b" | ... | "z" | "A" | "B" | ... | "Z"
<digit> ::= "0" | "1" | ... | "9"
<letter-or-digit> ::= <letter> | <digit>
```

Язык стек-ориентированный. Поддерживает следующие операции:
- `<число>` -- запушить число на вершину стека
- `VARIABLE <имя переменной>` -- задекларировать 8-битную переменную
- `<имя переменной>` -- запушить адрес первой ячейки переменной
- `+ - / * %` -- 8-битные классические арифметические операции. (забираются 2 верхних элемента стека, пушится результат)
- `Q+ Q- Q/ Q* Q%` -- 32-битные аналоги, при которых верхние 8 элементов рассматриваются в качестве двух (по 4 байта) чисел. Результат операции также 32-битный. Пример подобной операции: `stack |AA FF CC DD 11 FF 33 FF|, operation - 'Q+' ==> stack |BC FF 00 DC|`  
- `> < = Q> Q< Q=` -- операции сравнения (8-битные и 32х-битные). Оба сравниваемых числа с вершины стека забираются и записывается результат: `TRUE => -1`, `FALSE => 0`
- `IF <statement> THEN` -- забираем число с вершины стека. Если оно не равно нулю, то выполняем код до соответсвущего вложенности THEN.
- `BEGIN <statement> UNTIL` -- выполняем <statement>. Смотрим - если по результатам выполнения на вершине стека лежит 0, то выполняем ещё раз. 
- `SWAP QSWAP` -- меняем местами два верхних числа (8бит, 32бит)
- `DUP QDUP` -- дублируем два верхних числа (8бит, 32бит)
- `DROP QDROP` -- извлекаем число с вершины стека (8бит, 32бит)
- `OVER QOVER` -- запихиваем предпоследнее число на стеке на вершину стека
- `! Q!` -- вершина стека (два числа по 8 бит) забирается и используется в качестве адреса памяти. Следующее число (8 бит или 32 бит) используется в качестве значения.
- `@ Q@` -- забираем вершину стека (два числа по 8 бит) и используем его в качестве адреса. На стек пишется число лежащее по адресу (8 бит или 32 бит)
- `.` -- вывести вершину стека
- `ACCEPT` -- прочитать с ввода


## Организация памяти

Память разделена на память команд, память данных и стек.
Все 3 вида памяти представляют собой 8-битные ячейки памяти с 16-битной адресацией.

### Память команд
Реализуется списком словарей, описывающих инструкции
- Безадресные команды занимают 1 машинное слово. 
- Адресные (LOAD, SAVE, JMP, JZ, JNZ, JL) три машинных слова - `|OPCODE|HIGH_ADDRESS_BITS|LOW_ADDRESS_BITS|`.

### Память данных
Адресуется 16 битным линейным адресным пространством начиная с `0x0000` и заканчивая `0xFFFF`.
- Машинное слово - 8 бит
- Реализуется списком чисел.

### Стек
Отчасти автоматизированная память. Состоит из непосредственно стековой памяти с 16-битной адресацией, и 8-бит машинным 
словом TOS (top-of-stack) регистра и SP (stack pointer). Может отдавать значения из TOS и Стека по SP одновременно.


## Система команд

Особенности процессора:

- Машинное слово -- 8 бит, беззнаковое.
- Регистр указателя стека: `sp`:
    - может быть подан на правый вход `ALU`
    - может быть записан с выхода `ALU`
    - 12 бит
- Ввод-вывод -- порты ввода/вывода, токенизирован, символьный
- `pc` -- счётчик команд:
    - инкрементируется после каждой инструкции и может быть сложен с адресным регистром декодера если открыт соответствующий вентиль
- `decoder` -- имеет два регистра:
    - `address` -- адресный регистр, который устанавливается для некоторых команд по результату декодирования инструкции
    - `instruction` -- регистр, содержащий код инструкции, который используется контрольным юнитом `CU` 

### Набор инструкций

| Команда | Адресная? | Тип           | Кол-во тактов <br/>(выполнение) | Описание                                                                             |
|---------|-----------|---------------|---------------------------------|--------------------------------------------------------------------------------------|
| LOAD    | Да        | memory access |                                 | Загрузить на стек значение по адресу                                                 |
| SAVE    | Да        | memory access |                                 | Выгрузить вершину стека в ячейку по адресу                                           |
| JMP     | Да        | flow control  |                                 | Прыгнуть на команду по адресу                                                        |
| JZ      | Да        | flow control  |                                 | Прыгнуть на команду по адресу, если ZF==1                                            |
| JNZ     | Да        | flow control  |                                 | Прыгнуть на команду по адресу, если ZF==0                                            |
| JL      | Да        | flow control  |                                 | Прыгнуть на команду по адресу, если NF==1                                            |
| CALL    | Да        | flow control  |                                 | Вызвать функцию по её адресу                                                         |
| RET     | Нет       | flow control  |                                 | Вернуться вниз по стеку вызовов и продолжить программу                               |
| SET     | Нет       | memory access |                                 | Сохранить значение ( 8 бит) в память, используя 2 верхних элемента как адрес         |
| QSET    | Нет       | memory access |                                 | Сохранить значение (32 бит) в памяти, используя 2 верхних элемента как адрес         |
| GET     | Нет       | memory access |                                 | Загрузить в стек значение ( 8 бит) из памяти, используя 2 верхних элемента как адрес |
| QGET    | Нет       | memory access |                                 | Загрузить в стек значение (32 бит) из памяти, используя 2 верхних элемента как адрес |
| ADD     | Нет       | arithmetic    | +                               | 8-битное сложение                                                                    |
| SUB     | Нет       | arithmetic    | +                               | 8-битное вычитание                                                                   |
| DIV     | Нет       | arithmetic    | +                               | 8-битное деление                                                                     |
| MUL     | Нет       | arithmetic    | +                               | 8-битное умножение                                                                   |
| MOD     | Нет       | arithmetic    | +                               | 8-битное деление по модулю                                                           |
| INC     | Нет       | arithmetic    | +                               | 8-битное инкремент                                                                   |
| DEC     | Нет       | arithmetic    | +                               | 8-битное декремент                                                                   |
| SWAP    | Нет       | logic         | +                               | Поменять местами два верхних элемента стека                                          |
| OVER    | Нет       | logic         | +                               | Продублировать предпоследний элемент стека                                           |
| DUP     | Нет       | logic         | +                               | Продублировать последний элемент стека                                               |
| DROP    | Нет       | logic         | +                               | Выкинуть вершину стека                                                               |
| HLT     | Нет       | flow control  |                                 | Завершение работы программы                                                          |



### Кодирование инструкций

- Машинный код сохраняется как список JSON.
- Один элемент списка - одно машинное слово
- Индекс списка -- адрес инструкции. Используется для команд перехода.
- Адресные инструкции занимают 3 элемента списка, безадресные 

Пример:

```json
[
    {
        "value": "LOAD", 
        "related_token_index": 0
    },
    {
        "value": "0xBB",
        "related_token_index": 0
    },
    {
        "value": "0xCC",
        "related_token_index": 0
    },
    {
        "value": "DUP",
        "related_token_index": 1
    },
    { 
        "value": "HLT",
        "related_token_index": -1
    }
]
```

Где:

- `value` -- машинное слово. Либо это команда, либо это адрес для адресной команды
- `related_token_index` -- индекс токена, в результате чтения которого была добавлена эта инструкция.

## Транслятор

Интерфейс командной строки: `translator.py <input_file> <target_file>"`

Реализовано в модуле: [translator.py](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/src/translator.py)

Этапы трансляции (функция `translate`):

1. Трансформирование текста в последовательность значимых токенов.
2. Пре-преверка на неправильные последовательности конструкций языка (IF--THEN, BEGIN--UNTIL), вывод предупреждений (возможное деление на 0).
3. Генерация машинного кода.

Правила генерации машинного кода:

- для команд, однозначно соответствующих инструкциям -- прямое отображение;
- для команд, вызывающих добавление числа на вершину стека -- добавление в память ячейки с этим числом и добавление в список команд инструкции `PUSH` с соответствуюшим адресом. (если включена оптимизация, то перед добавлением будет произведен поиск по константам и, в случае нахождения идентичного значения - новой ячейки в памяти не появится, инструкция использует адрес константы)
- для декларации переменной -- проверка имени на допустимость (запрещено передекларирование, цифровое имя переменной, отсутствие имени, пересечение с символами языка)
- для ветвлений -- проверка парности. С входом в точку ветвления идёт запоминание количества добавленных инструкций, после чего добавленные инструкции окружаются соответствующими инструкциями ветвления.
- для циклов -- проверка парности. С входом в цикл аналогично ветлвениям запоминается количество добавленных инструкций, после чего добавляются инструкции ветвления.

## Модель процессора

Реализовано в модуле: [machine.py](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/src/machine.py).

![Image alt](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/Схема.png)

Примечание по схеме: красным обозначены порты входа/выхода, синим - сигналы выбора исходящие от CU, черным - шины данных, серым - сигналы флагов ALU

Память данных (RAM)
- реализована в классе RAM
- `latch_address` -- защёлкивание адреса. Может быть защёлкнут либо с выхода `ALU`, либо с адресного регистра `декодера`
- вывод может осуществляться либо на правый вход `ALU`, либо на порт вывода
- ввод может осуществляться либо с выхода `ALU`, либо с порта ввода
- управление сигналами для выбора направлений ввода/вывода реализованы в рамках python

Память инструкций
- представленна в виде списка структур. Доступ к её ячейкам осуществляется только в рамках цикла выборки инструкции по счетчику команд (значение счетчика команд используется как индекс в списке).
- вывод идёт на декодер, который просто разбивает структуру на код команды и, если нужно, адрес, содержащийся в инструкции.
- перед выбором инструкции (в зависимости от состояния вентиля и флагов аккумулятора) счетчик команд может быть сложен с адресом декодированной инструкции
- в конце каждой выборки инструкции идёт инкрементация счетчика команд.

ALU
- реализована в классе ALU
- в зависимости от сигналов управляющего юнита выполняет различные операции с правым и/или левым входом (в том числе простое перенаправление)
- установка сигналов реализована в рамках python
- выбором подающихся значений на правый и левый входы, а также направлением вывода занимается управляющий юнит

CU (control unit, управляющий юнит)
- реализован в классе ControlUnit
- занимается установкой управляющих сигналов (т.с. выполнением команд), реализовано в рамках python

Симуляция
- происходит в классе Simulation в методе simulate
- состоит из чередующихся между собой выборки инструкции и её выполнения
- заканчивается либо при возникновении критической ошибки (попытка прочитать пустой входной буфер/обращение к памяти по недопустимому адресу/деление на 0), либо выполнением команды `HTL`


## Апробация

В качестве тестов использовано три алгоритма:

1. вывод 'Hello world!'
2. подсчет и вывод суммы всех натуральных чисел от 1 до 999 включительно являющихся делителями 3 и/или 5
3. программа `cat`, повторяем ввод на выводе.

Интеграционные тесты реализованы тут: [test](./test) в трех вариантах:

- Golden Tests (проверка стандартного вывода программ)
- Unit Tests (проверка отдельных частей кода)
- Integration Test (проверка как разные кодовые базы взаимодействуют между собой)

CI:

``` yaml
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v2
      
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
         python -m pip install --upgrade pip
         pip install -r requirements.txt
        
    - name: test translator
      run: |
        python -m unittest -v -b test/unittests/TestTranslator.py 

    - name: test simulation
      run: |
        python -m unittest -v -b test/unittests/TestSimulation.py 

    - name: test golden tests
      run: |
        pytest 

    - name: test integration
      run: |
        python -m unittest -v -b test/integrational/TestAll.py 

```

Пример использования и журнал работы процессора на примере `hello world`:

``` console
> cat hello_world.forth
72 . 101 . 108 . 108 . 111 . 32 . 119 . 111 . 114 . 108 . 100 . 33 .
> python src/translator.py hello_world.forth
SOURCE CODE:
72 . 101 . 108 . 108 . 111 . 32 . 119 . 111 . 114 . 108 . 100 . 33 .

===== translation start =====
TRANSLATION (0): token: 72
TRANSLATION (1): token: .
TRANSLATION (2): token: 101
TRANSLATION (3): token: .
TRANSLATION (4): token: 108
TRANSLATION (5): token: .
TRANSLATION (6): token: 108
TRANSLATION (7): token: .
TRANSLATION (8): token: 111
TRANSLATION (9): token: .
TRANSLATION (10): token: 32
TRANSLATION (11): token: .
TRANSLATION (12): token: 119
TRANSLATION (13): token: .
TRANSLATION (14): token: 111
TRANSLATION (15): token: .
TRANSLATION (16): token: 114
TRANSLATION (17): token: .
TRANSLATION (18): token: 108
TRANSLATION (19): token: .
TRANSLATION (20): token: 100
TRANSLATION (21): token: .
TRANSLATION (22): token: 33
TRANSLATION (23): token: .
Len instructions: 25; Len data: 11
===== translation end =====


Translated code:
{'instructions': [{'opcode': 'PUSH', 'address': 2050, 'related_token_index': 0}, {'opcode': 'PRINT', 'related_token_index': 1}, {'opcode': 'PUSH', 'address': 2051, 'related_token_index': 2}, {'opcode': 'PRINT', 'related_token_index': 3}, {'opcode': 'PUSH', 'address': 2052, 'related_token_index': 4}, {'opcode': 'PRINT', 'related_token_index': 5}, {'opcode': 'PUSH', 'address': 2052, 'related_token_index': 6}, {'opcode': 'PRINT', 'related_token_index': 7}, {'opcode': 'PUSH', 'address': 2053, 'related_token_index': 8}, {'opcode': 'PRINT', 'related_token_index': 9}, {'opcode': 'PUSH', 'address': 2054, 'related_token_index': 10}, {'opcode': 'PRINT', 'related_token_index': 11}, {'opcode': 'PUSH', 'address': 2055, 'related_token_index': 12}, {'opcode': 'PRINT', 'related_token_index': 13}, {'opcode': 'PUSH', 'address': 2053, 'related_token_index': 14}, {'opcode': 'PRINT', 'related_token_index': 15}, {'opcode': 'PUSH', 'address': 2056, 'related_token_index': 16}, {'opcode': 'PRINT', 'related_token_index': 17}, {'opcode': 'PUSH', 'address': 2052, 'related_token_index': 18}, {'opcode': 'PRINT', 'related_token_index': 19}, {'opcode': 'PUSH', 'address': 2057, 'related_token_index': 20}, {'opcode': 'PRINT', 'related_token_index': 21}, {'opcode': 'PUSH', 'address': 2058, 'related_token_index': 22}, {'opcode': 'PRINT', 'related_token_index': 23}, {'opcode': 'HLT'}], 'data': [-1, 0, 72, 101, 108, 111, 32, 119, 114, 100, 33]}

PUSH 0x802
PRINT
PUSH 0x803
PRINT
PUSH 0x804
PRINT
PUSH 0x804
PRINT
PUSH 0x805
PRINT
PUSH 0x806
PRINT
PUSH 0x807
PRINT
PUSH 0x805
PRINT
PUSH 0x808
PRINT
PUSH 0x804
PRINT
PUSH 0x809
PRINT
PUSH 0x80a
PRINT
HLT


[-1, 0, 72, 101, 108, 111, 32, 119, 114, 100, 33]

Process finished with exit code 0

> cat program.bin 
{                                   
    "instructions": [               
        {                           
            "opcode": "PUSH",       
            "address": 2050,        
            "related_token_index": 0
        },                          
        {                           
            "opcode": "PRINT",      
            "related_token_index": 1
        },
        {
            "opcode": "PUSH",
            "address": 2051,
            "related_token_index": 2
        },
        {
            "opcode": "PRINT",
            "related_token_index": 3
        },
        {
            "opcode": "PUSH",
            "address": 2052,
            "related_token_index": 4
        },
        {
            "opcode": "PRINT",
            "related_token_index": 5
        },
        {
            "opcode": "PUSH",
            "address": 2052,
            "related_token_index": 6
        },
        {
            "opcode": "PRINT",
            "related_token_index": 7
        },
        {
            "opcode": "PUSH",
            "address": 2053,
            "related_token_index": 8
        },
        {
            "opcode": "PRINT",
            "related_token_index": 9
        },
        {
            "opcode": "PUSH",
            "address": 2054,
            "related_token_index": 10
        },
        {
            "opcode": "PRINT",
            "related_token_index": 11
        },
        {
            "opcode": "PUSH",
            "address": 2055,
            "related_token_index": 12
        },
        {
            "opcode": "PRINT",
            "related_token_index": 13
        },
        {
            "opcode": "PUSH",
            "address": 2053,
            "related_token_index": 14
        },
        {
            "opcode": "PRINT",
            "related_token_index": 15
        },
        {
            "opcode": "PUSH",
            "address": 2056,
            "related_token_index": 16
        },
        {
            "opcode": "PRINT",
            "related_token_index": 17
        },
        {
            "opcode": "PUSH",
            "address": 2052,
            "related_token_index": 18
        },
        {
            "opcode": "PRINT",
            "related_token_index": 19
        },
        {
            "opcode": "PUSH",
            "address": 2057,
            "related_token_index": 20
        },
        {
            "opcode": "PRINT",
            "related_token_index": 21
        },
        {
            "opcode": "PUSH",
            "address": 2058,
            "related_token_index": 22
        },
        {
            "opcode": "PRINT",
            "related_token_index": 23
        },
        {
            "opcode": "HLT"
        }
    ],
    "data": [
        -1,
        0,
        72,
        101,
        108,
        111,
        32,
        119,
        114,
        100,
        33
    ]
}

> ./machine.py target.out examples/foo_input.txt out.txt
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0001 -> PC: 0x001 | SP: 0x000 | AC: +00000 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 0
DEBUG:root:tick = 0002 -> PC: 0x001 | SP: 0x000 | AC: +00000 | ALU flags: zf=False nf=False of=False | RAM addr:0x802 ||| related token index: 0
DEBUG:root:tick = 0003 -> PC: 0x001 | SP: 0x000 | AC: +00072 | ALU flags: zf=False nf=False of=False | RAM addr:0x802 ||| related token index: 0
DEBUG:root:tick = 0004 -> PC: 0x001 | SP: 0x000 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 0
DEBUG:root:tick = 0005 -> PC: 0x001 | SP: 0x000 | AC: +00072 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 0
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0007 -> PC: 0x002 | SP: 0x000 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 1
DEBUG:root:tick = 0008 -> PC: 0x002 | SP: 0x000 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 1
DEBUG:root:tick = 0009 -> PC: 0x002 | SP: 0x-01 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 1
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0011 -> PC: 0x003 | SP: 0x000 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 2
DEBUG:root:tick = 0012 -> PC: 0x003 | SP: 0x000 | AC: +00072 | ALU flags: zf= True nf=False of=False | RAM addr:0x803 ||| related token index: 2
DEBUG:root:tick = 0013 -> PC: 0x003 | SP: 0x000 | AC: +00101 | ALU flags: zf=False nf=False of=False | RAM addr:0x803 ||| related token index: 2
DEBUG:root:tick = 0014 -> PC: 0x003 | SP: 0x000 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 2
DEBUG:root:tick = 0015 -> PC: 0x003 | SP: 0x000 | AC: +00101 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 2
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0017 -> PC: 0x004 | SP: 0x000 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 3
DEBUG:root:tick = 0018 -> PC: 0x004 | SP: 0x000 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 3
DEBUG:root:tick = 0019 -> PC: 0x004 | SP: 0x-01 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 3
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0021 -> PC: 0x005 | SP: 0x000 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 4
DEBUG:root:tick = 0022 -> PC: 0x005 | SP: 0x000 | AC: +00101 | ALU flags: zf= True nf=False of=False | RAM addr:0x804 ||| related token index: 4
DEBUG:root:tick = 0023 -> PC: 0x005 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x804 ||| related token index: 4
DEBUG:root:tick = 0024 -> PC: 0x005 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 4
DEBUG:root:tick = 0025 -> PC: 0x005 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 4
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0027 -> PC: 0x006 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 5
DEBUG:root:tick = 0028 -> PC: 0x006 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 5
DEBUG:root:tick = 0029 -> PC: 0x006 | SP: 0x-01 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 5
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0031 -> PC: 0x007 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 6
DEBUG:root:tick = 0032 -> PC: 0x007 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x804 ||| related token index: 6
DEBUG:root:tick = 0033 -> PC: 0x007 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x804 ||| related token index: 6
DEBUG:root:tick = 0034 -> PC: 0x007 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 6
DEBUG:root:tick = 0035 -> PC: 0x007 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 6
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0037 -> PC: 0x008 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 7
DEBUG:root:tick = 0038 -> PC: 0x008 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 7
DEBUG:root:tick = 0039 -> PC: 0x008 | SP: 0x-01 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 7
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0041 -> PC: 0x009 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 8
DEBUG:root:tick = 0042 -> PC: 0x009 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x805 ||| related token index: 8
DEBUG:root:tick = 0043 -> PC: 0x009 | SP: 0x000 | AC: +00111 | ALU flags: zf=False nf=False of=False | RAM addr:0x805 ||| related token index: 8
DEBUG:root:tick = 0044 -> PC: 0x009 | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 8
DEBUG:root:tick = 0045 -> PC: 0x009 | SP: 0x000 | AC: +00111 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 8
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0047 -> PC: 0x00a | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 9
DEBUG:root:tick = 0048 -> PC: 0x00a | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 9
DEBUG:root:tick = 0049 -> PC: 0x00a | SP: 0x-01 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 9
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0051 -> PC: 0x00b | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 10
DEBUG:root:tick = 0052 -> PC: 0x00b | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x806 ||| related token index: 10
DEBUG:root:tick = 0053 -> PC: 0x00b | SP: 0x000 | AC: +00032 | ALU flags: zf=False nf=False of=False | RAM addr:0x806 ||| related token index: 10
DEBUG:root:tick = 0054 -> PC: 0x00b | SP: 0x000 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 10
DEBUG:root:tick = 0055 -> PC: 0x00b | SP: 0x000 | AC: +00032 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 10
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0057 -> PC: 0x00c | SP: 0x000 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 11
DEBUG:root:tick = 0058 -> PC: 0x00c | SP: 0x000 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 11
DEBUG:root:tick = 0059 -> PC: 0x00c | SP: 0x-01 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 11
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0061 -> PC: 0x00d | SP: 0x000 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 12
DEBUG:root:tick = 0062 -> PC: 0x00d | SP: 0x000 | AC: +00032 | ALU flags: zf= True nf=False of=False | RAM addr:0x807 ||| related token index: 12
DEBUG:root:tick = 0063 -> PC: 0x00d | SP: 0x000 | AC: +00119 | ALU flags: zf=False nf=False of=False | RAM addr:0x807 ||| related token index: 12
DEBUG:root:tick = 0064 -> PC: 0x00d | SP: 0x000 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 12
DEBUG:root:tick = 0065 -> PC: 0x00d | SP: 0x000 | AC: +00119 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 12
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0067 -> PC: 0x00e | SP: 0x000 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 13
DEBUG:root:tick = 0068 -> PC: 0x00e | SP: 0x000 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 13
DEBUG:root:tick = 0069 -> PC: 0x00e | SP: 0x-01 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 13
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0071 -> PC: 0x00f | SP: 0x000 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 14
DEBUG:root:tick = 0072 -> PC: 0x00f | SP: 0x000 | AC: +00119 | ALU flags: zf= True nf=False of=False | RAM addr:0x805 ||| related token index: 14
DEBUG:root:tick = 0073 -> PC: 0x00f | SP: 0x000 | AC: +00111 | ALU flags: zf=False nf=False of=False | RAM addr:0x805 ||| related token index: 14
DEBUG:root:tick = 0074 -> PC: 0x00f | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 14
DEBUG:root:tick = 0075 -> PC: 0x00f | SP: 0x000 | AC: +00111 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 14
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0077 -> PC: 0x010 | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 15
DEBUG:root:tick = 0078 -> PC: 0x010 | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 15
DEBUG:root:tick = 0079 -> PC: 0x010 | SP: 0x-01 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 15
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0081 -> PC: 0x011 | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 16
DEBUG:root:tick = 0082 -> PC: 0x011 | SP: 0x000 | AC: +00111 | ALU flags: zf= True nf=False of=False | RAM addr:0x808 ||| related token index: 16
DEBUG:root:tick = 0083 -> PC: 0x011 | SP: 0x000 | AC: +00114 | ALU flags: zf=False nf=False of=False | RAM addr:0x808 ||| related token index: 16
DEBUG:root:tick = 0084 -> PC: 0x011 | SP: 0x000 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 16
DEBUG:root:tick = 0085 -> PC: 0x011 | SP: 0x000 | AC: +00114 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 16
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0087 -> PC: 0x012 | SP: 0x000 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 17
DEBUG:root:tick = 0088 -> PC: 0x012 | SP: 0x000 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 17
DEBUG:root:tick = 0089 -> PC: 0x012 | SP: 0x-01 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 17
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0091 -> PC: 0x013 | SP: 0x000 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 18
DEBUG:root:tick = 0092 -> PC: 0x013 | SP: 0x000 | AC: +00114 | ALU flags: zf= True nf=False of=False | RAM addr:0x804 ||| related token index: 18
DEBUG:root:tick = 0093 -> PC: 0x013 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x804 ||| related token index: 18
DEBUG:root:tick = 0094 -> PC: 0x013 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 18
DEBUG:root:tick = 0095 -> PC: 0x013 | SP: 0x000 | AC: +00108 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 18
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0097 -> PC: 0x014 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 19
DEBUG:root:tick = 0098 -> PC: 0x014 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 19
DEBUG:root:tick = 0099 -> PC: 0x014 | SP: 0x-01 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 19
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0101 -> PC: 0x015 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 20
DEBUG:root:tick = 0102 -> PC: 0x015 | SP: 0x000 | AC: +00108 | ALU flags: zf= True nf=False of=False | RAM addr:0x809 ||| related token index: 20
DEBUG:root:tick = 0103 -> PC: 0x015 | SP: 0x000 | AC: +00100 | ALU flags: zf=False nf=False of=False | RAM addr:0x809 ||| related token index: 20
DEBUG:root:tick = 0104 -> PC: 0x015 | SP: 0x000 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 20
DEBUG:root:tick = 0105 -> PC: 0x015 | SP: 0x000 | AC: +00100 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 20
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0107 -> PC: 0x016 | SP: 0x000 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 21
DEBUG:root:tick = 0108 -> PC: 0x016 | SP: 0x000 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 21
DEBUG:root:tick = 0109 -> PC: 0x016 | SP: 0x-01 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 21
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PUSH
INFO:root:----- PUSH -----
DEBUG:root:tick = 0111 -> PC: 0x017 | SP: 0x000 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 22
DEBUG:root:tick = 0112 -> PC: 0x017 | SP: 0x000 | AC: +00100 | ALU flags: zf= True nf=False of=False | RAM addr:0x80a ||| related token index: 22
DEBUG:root:tick = 0113 -> PC: 0x017 | SP: 0x000 | AC: +00033 | ALU flags: zf=False nf=False of=False | RAM addr:0x80a ||| related token index: 22
DEBUG:root:tick = 0114 -> PC: 0x017 | SP: 0x000 | AC: +00033 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 22
DEBUG:root:tick = 0115 -> PC: 0x017 | SP: 0x000 | AC: +00033 | ALU flags: zf=False nf=False of=False | RAM addr:0x000 ||| related token index: 22
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: PRINT
DEBUG:root:----- PRINT -----
DEBUG:root:tick = 0117 -> PC: 0x018 | SP: 0x000 | AC: +00033 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 23
DEBUG:root:tick = 0118 -> PC: 0x018 | SP: 0x000 | AC: +00033 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 23
DEBUG:root:tick = 0119 -> PC: 0x018 | SP: 0x-01 | AC: +00033 | ALU flags: zf= True nf=False of=False | RAM addr:0x000 ||| related token index: 23
INFO:root:=====   instruction fetch   =====
DEBUG:root:decoded instruction opcode: HLT
DEBUG:root:----- HLT -----
INFO:root:HLT INTERRUPTION
INFO:root:INSTRUCTION COUNTER: 24

> cat out.txt
Hello world!
```

| ФИО                     | алг.  | LoC       | code байт | code инстр. | инстр. | такт. | вариант |
|-------------------------|-------|-----------|-----------|-------------|--------|-------|---------|
| Андросов Иван Сергеевич | hello | 1         | -         | 25          | 24     | 119   | forth | stack | harv | hw | tick | struct | stream | port | prob1     |
| Андросов Иван Сергеевич | cat   | 1         | -         | 65          | 846    | 3975  | forth | stack | harv | hw | tick | struct | stream | port | prob1     |
| Андросов Иван Сергеевич | prob1 | 34        | -         | 145         | 52480  | 245784 | forth | stack | harv | hw | tick | struct | stream | port | prob1     |
