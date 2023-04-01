variable sum
0 sum !
variable i
0 i !
BEGIN
    i @ 1 + i !

    i @ 3 % 0 =
    i @ 5 % 0 =
    +
    IF
        i @ sum @ + sum !
    THEN

    i @ 999 =
UNTIL


variable i
0 i !
BEGIN
    sum @ 10 %
    sum @ 10 / sum !

    i @ 1 + i !

    sum @ 0 =
UNTIL

BEGIN
    48 + .

    i @ 1 - i !
    i @ 0 =
UNTIL
