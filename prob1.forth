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
sum @
