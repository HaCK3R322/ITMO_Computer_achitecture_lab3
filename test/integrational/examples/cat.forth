variable str_ptr
ACCEPT str_ptr !

variable i
0 i !

BEGIN
    str_ptr @ i @ + @

    dup
    IF
        dup
        .
    THEN

    i @ 1 + i !

    0 =
UNTIL

