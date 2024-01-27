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

:prob1
    tvariable target target t!

    tvariable sum
    0 0 0 sum t!
    tvariable i
    0 0 0 i t!

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

        i t@ target t@ t=
    UNTIL

    sum t@
;

:print_unsigned_tnumber
    variable start_pointer 0 start_pointer !
    variable len 0 len !

    BEGIN
        tdup 0 0 10 t%

        0 start_pointer @ ! drop drop
        start_pointer @ 1 + start_pointer !

        0 0 10 t/

        tdup 0 0 0 t=
    UNTIL

    drop drop drop

    BEGIN
        start_pointer @ 1 - start_pointer !

        0 start_pointer @ @
        48 + .

        start_pointer @ 0 =
    UNTIL

;

:main
    999 prob1
    print_unsigned_tnumber
; main