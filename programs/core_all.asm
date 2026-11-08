; core_all.asm - every instruction and pseudo-instruction at least once (used by tb_core)
        LI    R1, 0x0C      ; R1 = 12
        LI    R2, 0x05      ; R2 = 5
        ADD   R3, R1, R2    ; R3 = 17 (0x11)
        SUB   R4, R2, R1    ; R4 = 5 - 12 = 0xF9 (borrow)
        AND   R5, R1, R2    ; R5 = 0x04
        OR    R6, R1, R2    ; R6 = 0x0D
        XOR   R7, R1, R2    ; R7 = 0x09
        STORE R3, [0x20]    ; Mem[0x20] = 0x11
        NOR   R3, R1, R2    ; R3 = ~0x0D = 0xF2
        STORE R3, [0x21]    ; Mem[0x21] = 0xF2
        LI    R3, 2
        SLL   R4, R2, R3    ; R4 = 5 << 2 = 0x14
        SRL   R5, R1, R3    ; R5 = 12 >> 2 = 0x03
        STORE R4, [0x22]
        STORE R5, [0x23]
        LOAD  R6, [0x20]    ; R6 = 0x11
        ADDI  R6, R6, -1    ; R6 = 0x10
        ADDI  R6, R6, 31    ; R6 = 0x2F
        STORE R6, [0x24]
        MOV   R7, R6        ; R7 = 0x2F
        NOT   R7, R7        ; R7 = 0xD0
        STORE R7, [0x25]
        CLR   R4            ; R4 = 0
        NOP
        BEQ   R4, R0, skip1 ; taken: R4 == 0
        LI    R5, 0xEE      ; skipped
skip1:  BNE   R4, R0, bad   ; not taken
        LI    R5, 0x77      ; runs
        STORE R5, [0x26]    ; Mem[0x26] = 0x77
        LI    R1, 3         ; loop counter
        CLR   R2
loop:   ADDI  R2, R2, 2     ; R2 += 2
        ADDI  R1, R1, -1
        BNE   R1, R0, loop  ; backward branch, taken twice
        STORE R2, [0x27]    ; Mem[0x27] = 6
        JMP   done
bad:    LI    R5, 0xBA      ; must never run
        STORE R5, [0x26]
done:   BEQ   R1, R2, bad   ; not taken: 0 != 6
        HALT
