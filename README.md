# ITMO_Computer_architecture_lab3
Translator + Processor

# Forth. Транслятор и модель

- Андросов Иван Сергеевич P33111.
- `forth | stack | harv | hw | tick | struct | stream | port | pstr | prob1 | 8bit`


## Язык программирования

``` ebnf
program   = { statement } .
statement = 8bit-operation | 24bit-operation | control-flow | variable-operation .

8bit-operation      = number-operation | arithmetic-operation | comparison-operation | stack-operation .
24bit-operation     = number-24bit-operation | arithmetic-24bit-operation | comparison-24bit-operation | stack-24bit-operation .
control-flow        = if-statement | begin-until-statement | function-definition .
variable-operation  = variable-declaration .

number-operation    = "<" number ">" .
arithmetic-operation = "+" | "-" | "*" | "/" | "%" .
comparison-operation = ">" | "<" | "=" .
stack-operation     = "SWAP" | "DUP" | "DROP" | "OVER" | "ROT" | "TRUE" | "FALSE" | "!" | "@" | "." | "READ" .

number-24bit-operation      = "<" 24bit-number ">" .
arithmetic-24bit-operation = "t+" | "t/" | "t%" | "t=" .
comparison-24bit-operation = "t=" .
stack-24bit-operation      = "tdup" | "t!" | "t@" .

control-flow           = if-statement | begin-until-statement | function-definition .
if-statement           = "IF" statements "THEN" .
begin-until-statement = "BEGIN" statements "UNTIL" .
function-definition   = ":" function-name { statement } ";" .

variable-declaration   = "VARIABLE" variable-name .
variable-name          = identifier .

identifier             = letter { letter | digit } .
number                = digit { digit } .
24bit-number          = digit { digit } digit .

letter                = "a" | "b" | ... | "z" | "A" | "B" | ... | "Z" .
digit                 = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" .
```

Язык стек-ориентированный. Поддерживает следующие операции:

Обычные операции:

| операции                   | объяснение                                                                                |
|----------------------------|-------------------------------------------------------------------------------------------|
| <число>  [-128, 127]       | Положить на верхушку стека число.                                                         |
| `+` `-` `/` `*` `%`        | 8-битные арифметические операции                                                          |
| `>` `<` `=`                | Операции сравнения. По результатам в случае `True` будет лежать -1, в случае `False` 0    |
| `SWAP`                     | Меняет два верхних элемента местами. `a b c` -- `a c b`                                   |
| `DUP`                      | Дублирует верхний элемент. `a b c` -- `a b c c`                                           |
| `DROP`                     | Выкидывает верхний элемент. `a b c` -- `a b`                                              |
| `OVER`                     | Дублирует предпоследний элемент. `a b c` -- `a b c b`                                     |
| `ROT`                      | "Крутит" три верхние элемента. `a b c d` -- `a c d b`                                     |
| `TRUE`                     | Положить на вершину `-1`                                                                  |
| `FALSE`                    | Положить на вершину `0`                                                                   |
| `!`                        | Использует два верхних элемента как адрес и пишет по нему 3й. `a b c d` -- `a; MEM[cd]=b` |
| `@`                        | Использует два верхних элемента как адрес и читает с него. `a b c` -- `a MEM[bc]`         |
| `.`                        | Вывести верхний элемент как ASCII символ                                                  |
| `READ`                     | Считать с порта ввода символ на верхушку стека                                            |
| `:function_name`           | Начать задавать функцию                                                                   |
| `;`                        | Закончить задавать функцию                                                                |
| `IF` statements `THEN`     | Если на вершине не 0, то выполняем                                                        |
| `BEGIN` statements `UNTIL` | Выполняем как минимум один раз, если по результатам 0, то заново                          |
| `VARIABLE` var             | Объявить переменную                                                                       |
| var                        | Получить адрес переменной                                                                 |
| `"`                        | Добавить память в строку (до 127 символов) и получить адрес на неё                        |

Помимо обычных операций, на уровне транслятора (за исключением `t/` и `t%`) были добавлены операции для работы с
числами 24-битной длины:

| операции                                 | объяснение                                                                                                                |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| <число> [-8388608, -129], [128, 8388607] | Положить на верхушку стека число тройной величины в 3 ячейки<br/>Т.е. 8388607 будет представлено как `0x7F` `0xFF` `0xFF` |
| `t+` `t/` `t%`                           | 24-битные арифметические операции                                                                                         |
| `t=`                                     | Сравнить два 24-битных числа                                                                                              |
| `tdup`                                   | Дублирует верхнее 24-битное число                                                                                         |
| `t!`                                     | Используя 2 верхних элемента как адрес, записать по нему 24-битное число                                                  |
| `t@`                                     | Используя 2 верхних элемента как адрес, прочитать по нему 24-битное число                                                 |
| `TVARIABLE`                              | Объявить 24-битную переменную                                                                                             |

Видимость переменных: локальная. Внутри функций можно переопределять переменные.
т.е. после
```forth
VARIABLE var 15 var !
:func VARIABLE var 42 var ! ;
var @
```
На верхушке будет лежать 15.

Язык с обратной польской нотацией.


## Организация памяти

Память разделена на память команд, память данных, стек и стек возвратов
Все 3 вида памяти представляют собой 8-битные ячейки памяти с 16-битной адресацией.

### Память команд
Реализуется списком словарей, описывающих инструкции
- Машинное слово 8 бит
- 16-битная адресация
- Все команды занимают 1 машинное слово
- Ячейки с 0x0000 по 0x003F занимает таблица переходов LOAD
- Ячейки с 0x0040 по 0x007F занимает таблица переходов CALL
- Ячейки с 0x0080 по 0x00BF занимает таблица переходов JMP


| адреса | значения           |
|--------|--------------------|
| 0x0000 | LOAD start         |
| ...    |                    |
| 0x0040 | CALL start         |
| ...    |                    |
| 0x0080 | JMP start          |
| ...    |                    |
| 0x00С0 | instructions start |
| ...    |                    |
| 0xFFFF | LAST CELL          |


### Память данных
- Реализуется списком чисел
- Машинное слово 8 бит
- 16-битная адресация
- Логически разделена следующим образом:
  - Адреса `[0x0000; 0x07F5]` (2037 адресов) отведены для чего угодно хочет пользователь
  - Адреса `[0x07F6; 0x07FF]` (10 адресов) занимают указатели на другие логические участки
  - Адреса `[0x0800; 0x08FF]` (256 адресов) отведены под 8-битные константы
  - Адреса `[0x0900; 0x0BFF]` (724 адреса) отведены под 24-битные константы
  - Адреса `[0x0C00; 0x0DFF]` (512 адресов) отведены под адреса переменных
  - Адреса `[0x0E00; 0x10FF]` (724 адреса) отведены под переменные
  - Адреса `[0x1100; 0xFFFF]` (61184 адресов) отведены под строки

Таким образом, язык позволяет через код загрузить до 256 8-битных констант, до 256 24-битных констант, до 256 переменных
(8-бит или 24-бит), а также приличное количество строк

## Набор инструкций

Так как имеется довольно жесткое ограничение в виде 8-битной памяти, а делать CISC архитектуру с командами
в несколько машинных слов выглядит нездорово, у команд определена следующая архитектура:
- команды разделены на адресные и безадресные:
  - безадресные команды определяются старшими битами 111, по младшим битам вычисляется OPCODE инструкции. Т.е. они по
  формату выглядят примерно вот так: `111xxxxx`, где `xxxxx` определяет OPCODE (до 32х инструкций).
  - адресные команды выглядят вот так: `YYYxxxxx`, где `YYY` будет определять OPCODE инструкции (7 инструкций). 
  - `LOAD`, `CALL` и `JMPA` это прямая адресация.
  - `JMPR`, `JZ`, `JL`, `JO` это относительная.
  - При прямой адресации addr выступает офсетом в таблице адресов для этой команды (Так LOAD 4 будет иметь вид 0b`00000100`,
  OPCODE - `000`, OFFSET - `00100`, на стек загрузятся значения из памяти по адресам `0b0..001000` и `0b0..001001`
  - При относительной адрес складывается (или не складывается) с `PC` и получается "прыжок"


| Команда      | Адресная?                   | Тип           | Кол-во тактов <br/>(выполнение) | Влияние на стек/память        | Описание                                                                                                          |
|--------------|-----------------------------|---------------|---------------------------------|-------------------------------|-------------------------------------------------------------------------------------------------------------------|
| LOAD offset  | Да                          | memory access | 5                               | a b -- a b MEM[addr]          | Загрузить на стек значение по адресу, лежащему в offset таблицы LOAD                                              |
| JMPA offset  | Да                          | flow control  | 4                               | -                             | Прыгнуть на команду по по адресу, лежащему в offset таблицы JMPA                                                  |
| JMPR  offset | Да, относительная адресация | flow control  | 1                               | -                             | Перепрыгнуть через addr адресов                                                                                   |
| JZ   addr    | Да, относительная адресация | flow control  | 1                               | -                             | Перепрыгнуть через addr адресов, если ZF==1                                                                       |
| JL   addr    | Да, относительная адресация | flow control  | 1                               | -                             | Перепрыгнуть через addr адресов, если NF==1                                                                       |
| JO   addr    | Да, относительная адресация | flow control  | 1                               | -                             | Перепрыгнуть через addr адресов, если OF==1                                                                       |
| CALL addr    | Да                          | flow control  | 6                               | -                             | Вызвать функцию по по адресу, лежащему в offset таблицы CALL                                                      |
| RET          | Нет                         | flow control  | 2                               | -                             | Вернуться из функции                                                                                              |
| TRUE         | Нет                         | logic         | 1                               | a b -- b a -1                 | Положить на вершину стека `True` (0)                                                                              |
| FALSE        | Нет                         | logic         | 1                               | a b -- b a 0                  | Положить на вершину стека `False` (-1)                                                                            |
| CMP          | Нет                         | logic         | 1                               | -                             | Установить флаги по результатам сравнения двух верхних чисел. (ZF/NF: a == b -> 1/0; a > b -> 0/0; a < b -> 0/1 ) |
| SWAP         | Нет                         | logic         | 1                               | a b -- b a                    | Поменять местами два верхних элемента стека                                                                       |
| OVER         | Нет                         | logic         | 5                               | a b -- a b a                  | Продублировать предпоследний элемент стека                                                                        |
| DUP          | Нет                         | logic         | 1                               | a b -- a b b                  | Продублировать последний элемент стека                                                                            |
| DROP         | Нет                         | logic         | 1                               | a b -- a                      | Выкинуть вершину стека                                                                                            |
| ROT          | Нет                         | logic         | 4                               | a b c -- b c a                | Ротация 3х верхних элементов                                                                                      |
| TOR          | Нет                         | logic         | 1                               | S: a R: -- S: R: a            | Запушить TOS в RETURN STACK                                                                                       |
| RFROM        | Нет                         | logic         | 1                               | S: R: a -- S: a R:            | Запушить вершину RETURN STACK'a в STACK                                                                           |
| SET          | Нет                         | memory access | 3                               | a b c d -- a; MEM[cd]=b       | Сохранить значение ( 8 бит) в память, используя 2 верхних элемента как адрес                                      |
| GET          | Нет                         | memory access | 3                               | a b c -- a MEM[bc]            | Загрузить в стек значение ( 8 бит) из памяти, используя 2 верхних элемента как адрес                              |
| SUM          | Нет                         | arithmetic    | 1                               | a b -- a+b                    | 8-битное сложение                                                                                                 |
| SUB          | Нет                         | arithmetic    | 1                               | a b -- a-b                    | 8-битное вычитание                                                                                                |
| MUL          | Нет                         | arithmetic    | 1                               | a b -- a*b                    | 8-битное умножение                                                                                                |
| DIV          | Нет                         | arithmetic    | 1                               | a b -- a/b                    | 8-битное деление                                                                                                  |
| TDIV         | Нет                         | arithmetic    | 1                               | aaa bbb -- aaa/bbb            | 24-битное деление                                                                                                 |
| MOD          | Нет                         | arithmetic    | 1                               | a b -- a%b                    | 8-битное деление по модулю                                                                                        |
| TMOD         | Нет                         | arithmetic    | 1                               | aaa bbb -- aaa%bbb            | 24-битное деление по модулю                                                                                       |
| INC          | Нет                         | arithmetic    | 1                               | a b -- a ++b                  | 8-битное инкремент                                                                                                |
| DEC          | Нет                         | arithmetic    | 1                               | a b -- a --b                  | 8-битное декремент                                                                                                |
| READ         | Нет                         | IO            | 1                               | a b -- a b new_symbol         | Считать один символ с порта на вершину стека                                                                      |
| PRINT        | Нет                         | IO            | 1                               | a b -- a ; out_port.append(b) | Вывести вершину стека на порт                                                                                     |
| HLT          | Нет                         | flow control  | 1                               | -                             | Завершение работы программы                                                                                       |



### Кодирование инструкций

- Машинный код сохраняется как список JSON.
- Один элемент списка - одно машинное слово
- Индекс списка -- адрес инструкции.
- В случае адресных инструкций, имеется offset 

Пример:

```json
[
    {
      "value": "JZ",
      "related_token_index": 49,
      "related_token": "=",
      "offset": 4
    },
    {
      "value": "INC",
      "related_token_index": 47,
      "related_token": "1",
      "offset": null
    }
]
```

Где:

- `value` -- машинное слово. Либо это команда, либо это адрес для адресной команды
- `offset` -- офсет адресной инструкции
- `related_token_index` -- индекс токена, в результате чтения которого была добавлена эта инструкция.
- `related_token` -- сам токен, в результате чтения которого была добавлена эта инструкция.

## Транслятор

Интерфейс командной строки: `translator.py <input_file> <target_file>"`

Реализовано в модуле: [translatorv2.py](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/src/translatorv2.py)

Этапы трансляции (функция `translate`):

1. Трансформирование текста в последовательность значимых токенов.
2. Подготовка таблиц адресации и установка указателей в памяти
3. Генерация машинного кода.
4. Заполнение JMP таблицы для JMPA переходов if/then вне функций
5. Добавление функций в общий пул инструкций и заполнение CALL таблицы адресами функций
6. Заполнение JMP таблицы для JMPA переходов begin/until внутри функций
7. Заполнение JMP таблицы для JMPA переходов if/then внутри функций
8. Слияние таблиц переходов с общим пулом инструкций
9. Форматирование и сохранение в выходной файл инструкций и оперативной памяти

Правила генерации машинного кода:

- для команд, однозначно соответствующих инструкциям -- прямое отображение;
- для команд сравнения и прочих, не укладывающихся в одну инструкцию -- добавление необходимых инструкций
- константы (числа которые пушатся в стек) -- добавляются следующим образом:
  - в зависимости от того 8-битная это или 24-битная константа добавляется LOAD вызов адреса начала команд
  - добавляется столько инструкций инкремента, какой индекс будет у этой константы (итого на стеке лежит адрес первой ячейки константы)
  - если константа 8-битная, сразу забирается из стека командой @
  - если константа 24-битная, то алгоритмом забираются 3 ячейки
- объявление переменных - после ключевого слово `VARIABLE`/`TVARIABLE` следующий токен будет взят как её имя (если не пройдет проверку на имя, то ошибка). Для функций к имени добавится имя функции
- загрузка адреса переменной проходит схожим с константами образом
- определение функции -- резервирование CALL офсета и добавление сгенерированных инструкций по правилам выше в собственный пул функции (потом эти инструкции будут вставлены в общий пул на соответствующем этапе трансляции)


## Модель процессора

Реализовано в модуле: [model.py](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/src/model.py).

![Image alt](https://github.com/HaCK3R322/ITMO_Computer_achitecture_lab3/blob/master/Архитектура.png)

Примечание по схеме: синим обозначены `sel` сигналы от CU

Data bus:
- 8bit шина памяти
- реализована на уровне python, т.е. обмен данными переменных

ALU:
- Реализована в классе `ALU`
- Выполняет арифметические операции над TOS (top-of-stack) и NEXT (ячейка на которую указывает SP), результат складывает в TOS и устанавливаются (если надо) флаги

Стек:
- Автоматическая память (`push`, `pop`)
- Реализован в классе `Stack`
- Поддерживает:
  - Загрузку и выгрузку TOS
  - Инкремент, Декремент SP
  - Арифметические и другие операции между TOS и NEXT
  - `push` и `pop` со стеком возвратов

Стек возвратов:
- Тоже реализован в классе `Stack`
- Аналогичен стеку, за исключением того, что над ним не поддерживаются арифметические операции

Память команд (IMEM):
- Реализована в классе `IntructionMemory`
- Поддерживает 
  - Установку верхних и нижних бит адреса с шины данных
  - Установку адреса с PC (program counter)
  - Инкремент адреса
  - Установку вычисляемого по OPCODE и OFFSET адреса (в случае таблиц адресации)
  - Выгрузку и загрузку данных через шину данных

Оперативная память (RAM):
- Реализована в классе `RAM
- Поддерживает 
  - Установку верхних и нижних бит адреса с шины данных
  - Выгрузку и загрузку данных через шину данных

ControlUnit:
- реализован в классе `ControlUnit`

Decoder:
- реализован в классе `Decoder`

## Симуляция
- Происходит в классе `Simulation` в методе `simulate`
- Запускает цикл из 4 действий:
  1. Получение инструкции
  2. Декодинг
  3. Выполнение инструкции
  4. Инкеремент PC
- Останавливается при какой-либо ошибке (в т.ч. ошибки выброшенной HLT инструкцией)


## Апробация

В качестве тестов использовано 4 алгоритма:

1. программа `cat`, повторяем ввод на выводе.
2. вывод 'Hello world!'
3. подсчет и вывод суммы всех натуральных чисел от 1 до 999 включительно являющихся делителями 3 и/или 5
4. программа `hello_user_name` -- спросить юзернейм и вывести приветствие с именем

Интеграционные тесты реализованы тут: [test](./test) в трех вариантах:

- Golden Tests (проверка логов программ)
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
        python-version: '3.12'

    - name: Install dependencies
      run: |
         python -m pip install --upgrade pip
         pip install -r requirements.txt

    - name: run TRANSLATOR unit tests
      run: |
        python -m unittest -v -b test/unittests/translator/TestTranslator.py 

    - name: run MODEL unit tests
      run: |
        python -m unittest -v -b test/unittests/model/TestModel.py

    - name: run golden tests TRANSLATOR
      run: |
        python -m unittest -v -b test/golden/TestAllGoldenTranslator.py

    - name: run golden tests MODEL
      run: |
        python -m unittest -v -b test/golden/TestAllGoldenModel.py

    - name: run integrational tests
      run: |
        python -m unittest -v -b test/integrational/TestAll.py

```

Пример использования и журнал работы процессора на примере `cat`:

``` console
> cat cat.forth
read

begin
    read .
    1 - dup 0 =
until
> python source.forth program.lab
> cat src/log/translator/default_translator_logger/default_translator_logger.log
SOURCE CODE:
read

begin
    read .
    1 - dup 0 =
until

===== translation start =====
Writing to table LOAD table offset 0: imem[0000] = 07
Writing to table LOAD table offset 0: imem[0001] = F6
Writing to table LOAD table offset 1: imem[0002] = 07
Writing to table LOAD table offset 1: imem[0003] = F7
Writing to table LOAD table offset 2: imem[0004] = 07
Writing to table LOAD table offset 2: imem[0005] = F8
Writing to table LOAD table offset 3: imem[0006] = 07
Writing to table LOAD table offset 3: imem[0007] = F9
Writing to table LOAD table offset 4: imem[0008] = 07
Writing to table LOAD table offset 4: imem[0009] = FA
Writing to table LOAD table offset 5: imem[000A] = 07
Writing to table LOAD table offset 5: imem[000B] = FB
Writing to table LOAD table offset 6: imem[000C] = 07
Writing to table LOAD table offset 6: imem[000D] = FC
Writing to table LOAD table offset 7: imem[000E] = 07
Writing to table LOAD table offset 7: imem[000F] = FD
Writing to table LOAD table offset 8: imem[0010] = 07
Writing to table LOAD table offset 8: imem[0011] = FE
Writing to table LOAD table offset 9: imem[0012] = 07
Writing to table LOAD table offset 9: imem[0013] = FF
tokenized: ['READ', 'BEGIN', 'READ', '.', '1', '-', 'DUP', '0', '=', 'UNTIL']
Appending instruction READ
Appending instruction READ
Appending instruction PRINT
Appending instruction FALSE
Appending instruction INC
Appending instruction SUB
Appending instruction DUP
Appending instruction FALSE
Appending instruction CMP
Appending instruction JZ
Appending instruction DROP
Appending instruction DROP
Appending instruction FALSE
Appending instruction JMPR
Appending instruction DROP
Appending instruction DROP
Appending instruction TRUE
Processing UNTIL token outside of any function
Writing to table JMPA table offset 0: imem[0080] = 00
Writing to table JMPA table offset 0: imem[0081] = C0
Appending instruction FALSE
Appending instruction CMP
Appending instruction DROP
Appending instruction DROP
Appending instruction JZ
Appending instruction JMPR
Appending instruction JMPA
Appending instruction HLT
===== translation end =====

Total number of translated instructions: 25

> python machine.py progam.lab input.txt output.txt debug
Original input: "Hello world!"
Reversed input buffer:
    0: 33
    1: 100
    2: 108
    3: 114
    4: 111
    5: 119
    6: 32
    7: 111
    8: 108
    9: 108
    10: 101
    11: 72
    12: 12
]

Not void imem:
0x0000 | 0x0007
0x0001 | 0x00F6
0x0002 | 0x0007
0x0003 | 0x00F7
0x0004 | 0x0007
0x0005 | 0x00F8
0x0006 | 0x0007
0x0007 | 0x00F9
0x0008 | 0x0007
0x0009 | 0x00FA
0x000A | 0x0007
0x000B | 0x00FB
0x000C | 0x0007
0x000D | 0x00FC
0x000E | 0x0007
0x000F | 0x00FD
0x0010 | 0x0007
0x0011 | 0x00FE
0x0012 | 0x0007
0x0013 | 0x00FF
0x0081 | 0x00C0
0x00C0 | READ
0x00C1 | READ
0x00C2 | PRINT
0x00C3 | FALSE
0x00C4 | INC
0x00C5 | SUB
0x00C6 | DUP
0x00C7 | FALSE
0x00C8 | CMP
0x00C9 | JZ
0x00CA | DROP
0x00CB | DROP
0x00CC | FALSE
0x00CD | JMPR
0x00CE | DROP
0x00CF | DROP
0x00D0 | TRUE
0x00D1 | FALSE
0x00D2 | CMP
0x00D3 | DROP
0x00D4 | DROP
0x00D5 | JZ
0x00D6 | JMPR
0x00D7 | JMPA
0x00D8 | HLT

=== Simulation start ===
tick      1: STACK(sp==0xFFFF): |                    , 0x0C|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c0     PC: 0x00c0     rel_inst_index: 0 (READ, READ)
tick      2: STACK(sp==0x0000): |               0x0C , 0x48|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick      3: STACK(sp==0xFFFF): |                    , 0x0C|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick      4: STACK(sp==0x0000): |               0x0C , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick      5: STACK(sp==0x0000): |               0x0C , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick      6: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick      7: STACK(sp==0x0000): |               0x0B , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick      8: STACK(sp==0x0001): |          0x0B 0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick      9: STACK(sp==0x0001): |          0x0B 0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick     10: STACK(sp==0x0000): |               0x0B , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick     11: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick     12: STACK(sp==0x0000): |               0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick     13: STACK(sp==0x0000): |               0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick     14: STACK(sp==0x0001): |          0x0B      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick     15: STACK(sp==0x0001): |          0x0B      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick     16: STACK(sp==0x0000): |               0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick     17: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick     18: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick     19: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     20: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     21: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     22: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick     23: STACK(sp==0x0000): |               0x0B , 0x65|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick     24: STACK(sp==0xFFFF): |                    , 0x0B|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick     25: STACK(sp==0x0000): |               0x0B , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick     26: STACK(sp==0x0000): |               0x0B , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick     27: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick     28: STACK(sp==0x0000): |               0x0A , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick     29: STACK(sp==0x0001): |          0x0A 0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick     30: STACK(sp==0x0001): |          0x0A 0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick     31: STACK(sp==0x0000): |               0x0A , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick     32: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick     33: STACK(sp==0x0000): |               0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick     34: STACK(sp==0x0000): |               0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick     35: STACK(sp==0x0001): |          0x0A      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick     36: STACK(sp==0x0001): |          0x0A      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick     37: STACK(sp==0x0000): |               0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick     38: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick     39: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick     40: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     41: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     42: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     43: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick     44: STACK(sp==0x0000): |               0x0A , 0x6C|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick     45: STACK(sp==0xFFFF): |                    , 0x0A|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick     46: STACK(sp==0x0000): |               0x0A , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick     47: STACK(sp==0x0000): |               0x0A , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick     48: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick     49: STACK(sp==0x0000): |               0x09 , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick     50: STACK(sp==0x0001): |          0x09 0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick     51: STACK(sp==0x0001): |          0x09 0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick     52: STACK(sp==0x0000): |               0x09 , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick     53: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick     54: STACK(sp==0x0000): |               0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick     55: STACK(sp==0x0000): |               0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick     56: STACK(sp==0x0001): |          0x09      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick     57: STACK(sp==0x0001): |          0x09      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick     58: STACK(sp==0x0000): |               0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick     59: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick     60: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick     61: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     62: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     63: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     64: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick     65: STACK(sp==0x0000): |               0x09 , 0x6C|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick     66: STACK(sp==0xFFFF): |                    , 0x09|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick     67: STACK(sp==0x0000): |               0x09 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick     68: STACK(sp==0x0000): |               0x09 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick     69: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick     70: STACK(sp==0x0000): |               0x08 , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick     71: STACK(sp==0x0001): |          0x08 0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick     72: STACK(sp==0x0001): |          0x08 0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick     73: STACK(sp==0x0000): |               0x08 , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick     74: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick     75: STACK(sp==0x0000): |               0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick     76: STACK(sp==0x0000): |               0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick     77: STACK(sp==0x0001): |          0x08      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick     78: STACK(sp==0x0001): |          0x08      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick     79: STACK(sp==0x0000): |               0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick     80: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick     81: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick     82: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     83: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     84: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick     85: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick     86: STACK(sp==0x0000): |               0x08 , 0x6F|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick     87: STACK(sp==0xFFFF): |                    , 0x08|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick     88: STACK(sp==0x0000): |               0x08 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick     89: STACK(sp==0x0000): |               0x08 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick     90: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick     91: STACK(sp==0x0000): |               0x07 , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick     92: STACK(sp==0x0001): |          0x07 0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick     93: STACK(sp==0x0001): |          0x07 0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick     94: STACK(sp==0x0000): |               0x07 , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick     95: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick     96: STACK(sp==0x0000): |               0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick     97: STACK(sp==0x0000): |               0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick     98: STACK(sp==0x0001): |          0x07      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick     99: STACK(sp==0x0001): |          0x07      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    100: STACK(sp==0x0000): |               0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    101: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    102: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    103: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    104: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    105: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    106: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    107: STACK(sp==0x0000): |               0x07 , 0x20|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    108: STACK(sp==0xFFFF): |                    , 0x07|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    109: STACK(sp==0x0000): |               0x07 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    110: STACK(sp==0x0000): |               0x07 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    111: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    112: STACK(sp==0x0000): |               0x06 , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    113: STACK(sp==0x0001): |          0x06 0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    114: STACK(sp==0x0001): |          0x06 0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    115: STACK(sp==0x0000): |               0x06 , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    116: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    117: STACK(sp==0x0000): |               0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    118: STACK(sp==0x0000): |               0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    119: STACK(sp==0x0001): |          0x06      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    120: STACK(sp==0x0001): |          0x06      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    121: STACK(sp==0x0000): |               0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    122: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    123: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    124: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    125: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    126: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    127: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    128: STACK(sp==0x0000): |               0x06 , 0x77|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    129: STACK(sp==0xFFFF): |                    , 0x06|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    130: STACK(sp==0x0000): |               0x06 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    131: STACK(sp==0x0000): |               0x06 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    132: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    133: STACK(sp==0x0000): |               0x05 , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    134: STACK(sp==0x0001): |          0x05 0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    135: STACK(sp==0x0001): |          0x05 0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    136: STACK(sp==0x0000): |               0x05 , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    137: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    138: STACK(sp==0x0000): |               0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    139: STACK(sp==0x0000): |               0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    140: STACK(sp==0x0001): |          0x05      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    141: STACK(sp==0x0001): |          0x05      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    142: STACK(sp==0x0000): |               0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    143: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    144: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    145: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    146: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    147: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    148: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    149: STACK(sp==0x0000): |               0x05 , 0x6F|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    150: STACK(sp==0xFFFF): |                    , 0x05|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    151: STACK(sp==0x0000): |               0x05 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    152: STACK(sp==0x0000): |               0x05 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    153: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    154: STACK(sp==0x0000): |               0x04 , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    155: STACK(sp==0x0001): |          0x04 0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    156: STACK(sp==0x0001): |          0x04 0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    157: STACK(sp==0x0000): |               0x04 , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    158: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    159: STACK(sp==0x0000): |               0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    160: STACK(sp==0x0000): |               0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    161: STACK(sp==0x0001): |          0x04      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    162: STACK(sp==0x0001): |          0x04      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    163: STACK(sp==0x0000): |               0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    164: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    165: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    166: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    167: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    168: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    169: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    170: STACK(sp==0x0000): |               0x04 , 0x72|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    171: STACK(sp==0xFFFF): |                    , 0x04|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    172: STACK(sp==0x0000): |               0x04 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    173: STACK(sp==0x0000): |               0x04 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    174: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    175: STACK(sp==0x0000): |               0x03 , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    176: STACK(sp==0x0001): |          0x03 0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    177: STACK(sp==0x0001): |          0x03 0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    178: STACK(sp==0x0000): |               0x03 , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    179: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    180: STACK(sp==0x0000): |               0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    181: STACK(sp==0x0000): |               0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    182: STACK(sp==0x0001): |          0x03      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    183: STACK(sp==0x0001): |          0x03      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    184: STACK(sp==0x0000): |               0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    185: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    186: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    187: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    188: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    189: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    190: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    191: STACK(sp==0x0000): |               0x03 , 0x6C|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    192: STACK(sp==0xFFFF): |                    , 0x03|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    193: STACK(sp==0x0000): |               0x03 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    194: STACK(sp==0x0000): |               0x03 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    195: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    196: STACK(sp==0x0000): |               0x02 , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    197: STACK(sp==0x0001): |          0x02 0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    198: STACK(sp==0x0001): |          0x02 0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    199: STACK(sp==0x0000): |               0x02 , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    200: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    201: STACK(sp==0x0000): |               0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    202: STACK(sp==0x0000): |               0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    203: STACK(sp==0x0001): |          0x02      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    204: STACK(sp==0x0001): |          0x02      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    205: STACK(sp==0x0000): |               0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    206: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    207: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    208: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    209: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    210: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    211: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    212: STACK(sp==0x0000): |               0x02 , 0x64|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    213: STACK(sp==0xFFFF): |                    , 0x02|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    214: STACK(sp==0x0000): |               0x02 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    215: STACK(sp==0x0000): |               0x02 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    216: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    217: STACK(sp==0x0000): |               0x01 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    218: STACK(sp==0x0001): |          0x01 0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    219: STACK(sp==0x0001): |          0x01 0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    220: STACK(sp==0x0000): |               0x01 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00ca     PC: 0x00ca     rel_inst_index: 8 (=, DROP)
tick    221: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cb     PC: 0x00cb     rel_inst_index: 8 (=, DROP)
tick    222: STACK(sp==0x0000): |               0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cc     PC: 0x00cc     rel_inst_index: 8 (=, FALSE)
tick    223: STACK(sp==0x0000): |               0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00cd     PC: 0x00d0     rel_inst_index: 8 (=, JMPR)
tick    224: STACK(sp==0x0001): |          0x01      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    225: STACK(sp==0x0001): |          0x01      , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    226: STACK(sp==0x0000): |               0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    227: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    228: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d5     PC: 0x00d6     rel_inst_index: 9 (UNTIL, JMPR)
tick    229: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    230: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0080     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    231: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPA)
tick    232: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x0081     PC: 0x00c0     rel_inst_index: 9 (UNTIL, JMPA)
tick    233: STACK(sp==0x0000): |               0x01 , 0x21|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c1     PC: 0x00c1     rel_inst_index: 2 (READ, READ)
tick    234: STACK(sp==0xFFFF): |                    , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c2     PC: 0x00c2     rel_inst_index: 3 (., PRINT)
tick    235: STACK(sp==0x0000): |               0x01 , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c3     PC: 0x00c3     rel_inst_index: 4 (1, FALSE)
tick    236: STACK(sp==0x0000): |               0x01 , 0x01|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/0/0     IMEM.ADDR: 0x00c4     PC: 0x00c4     rel_inst_index: 4 (1, INC)
tick    237: STACK(sp==0xFFFF): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c5     PC: 0x00c5     rel_inst_index: 5 (-, SUB)
tick    238: STACK(sp==0x0000): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c6     PC: 0x00c6     rel_inst_index: 6 (DUP, DUP)
tick    239: STACK(sp==0x0001): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c7     PC: 0x00c7     rel_inst_index: 7 (0, FALSE)
tick    240: STACK(sp==0x0001): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c8     PC: 0x00c8     rel_inst_index: 8 (=, CMP)
tick    241: STACK(sp==0x0001): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00c9     PC: 0x00cd     rel_inst_index: 8 (=, JMPR)
tick    242: STACK(sp==0x0000): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00ce     PC: 0x00ce     rel_inst_index: 8 (=, DROP)
tick    243: STACK(sp==0xFFFF): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00cf     PC: 0x00cf     rel_inst_index: 8 (=, DROP)
tick    244: STACK(sp==0x0000): |                    , 0xFF|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d0     PC: 0x00d0     rel_inst_index: 8 (=, TRUE)
tick    245: STACK(sp==0x0001): |               0xFF , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 1/0/0     IMEM.ADDR: 0x00d1     PC: 0x00d1     rel_inst_index: 9 (UNTIL, FALSE)
tick    246: STACK(sp==0x0001): |               0xFF , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/1/0     IMEM.ADDR: 0x00d2     PC: 0x00d2     rel_inst_index: 9 (UNTIL, CMP)
tick    247: STACK(sp==0x0000): |                    , 0xFF|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/1/0     IMEM.ADDR: 0x00d3     PC: 0x00d3     rel_inst_index: 9 (UNTIL, DROP)
tick    248: STACK(sp==0xFFFF): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/1/0     IMEM.ADDR: 0x00d4     PC: 0x00d4     rel_inst_index: 9 (UNTIL, DROP)
tick    249: STACK(sp==0xFFFF): |                    , 0x00|     RSTACK(sp==65534): |                    ,     |    ZF/NF/OF: 0/1/0     IMEM.ADDR: 0x00d6     PC: 0x00d7     rel_inst_index: 9 (UNTIL, JMPR)
HLT was raised on tick 249
=== Simulation end. Ticks: 249. ===

Stack printed:
-------------
 TOS   | 0x00  ==  0

Output buffer: [
    0: H
    1: e
    2: l
    3: l
    4: o
    5:  
    6: w
    7: o
    8: r
    9: l
    10: d
    11: !
]
Output buffer jointed: "Hello world!"

> cat output.txt
Hello world!
```

| ФИО                     | алг.            | LoC | code байт | code инстр. | инстр. | такт.   | вариант                                                     |
|-------------------------|-----------------|-----|-----------|-------------|--------|---------|-------------------------------------------------------------|
| Андросов Иван Сергеевич | cat             | 6   | -         | 10          | 25     | 249     | forth,stack,harv,hw,tick,struct,stream,port,pstr,prob1,8bit |
| Андросов Иван Сергеевич | hello_world     | 29  | -         | 67          | 287    | 5481    | forth,stack,harv,hw,tick,struct,stream,port,pstr,prob1,8bit |
| Андросов Иван Сергеевич | hello_user_name | 37  | -         | 97          | 305    | 13246   | forth,stack,harv,hw,tick,struct,stream,port,pstr,prob1,8bit |
| Андросов Иван Сергеевич | prob1           | 72  | -         | 140         | 2010   | 1518359 | forth,stack,harv,hw,tick,struct,stream,port,pstr,prob1,8bit |
