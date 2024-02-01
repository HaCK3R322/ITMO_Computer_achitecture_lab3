:count_to_twenty
    0 IF 0xaa THEN
    -1 IF
        0 IF 0xbb THEN
        -1 IF

            0
            BEGIN
                0
                BEGIN
                    1 +

                    dup 5 =
                UNTIL

                +

                dup 20 =
            UNTIL
        THEN
    THEN
;

0
BEGIN
    count_to_twenty +

    dup 100 =
UNTIL