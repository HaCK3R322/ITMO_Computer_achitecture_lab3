tvariable sum
0 0 0 sum t!
tvariable i
0 0 0 i t!
:check_if_mod_3
    0 0 3
    t%
    0 0 0
    T=
;
:check_if_mod_5
    0 0 5
    t%
    0 0 0
    T=
;

:calc
    BEGIN
        i t@ 0 0 1 t+ i t!

        i t@
        check_if_mod_3
        i t@
        check_if_mod_5
        +
        if
            i t@ sum t@ t+ sum t!
        THEN

        i t@ 999 t=
    UNTIL

    sum t@
; calc

tvariable sum
0 0 0 sum t!
tvariable i
0 0 0 i t!
:check_if_mod_3
    0 0 3
    t%
    0 0 0
    T=
;
:check_if_mod_5
    0 0 5
    t%
    0 0 0
    T=
;

:calc
    BEGIN
        i t@ 0 0 1 t+ i t!

        i t@
        check_if_mod_3
        i t@
        check_if_mod_5
        +
        if
            i t@ sum t@ t+ sum t!
        THEN

        i t@ 0 0 9 t=
    UNTIL

    sum t@
;

:print_tconstant
    begin
        tdup 0 0 10 t%
        48 + . drop drop

        0 0 10 t/

        dup 0 =
    until
;