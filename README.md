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
