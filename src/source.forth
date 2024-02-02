:print_str
    variable string_address_high string_address_high !
    variable string_address_low string_address_low !
    variable i 1 i !

    string_address_low @ string_address_high @ @ if
        begin
            0 string_address_low @ string_address_high @
            0 0 i @ t+ @ .                                                      # i += 1
            drop

            i @ 1 + i !

            string_address_low @ string_address_high @ @                        # get len
            i @ 1 -
            =                                                                   # i == str_len - 1 ?
        until
    then
;

"Hello" print_str
" world!" print_str
