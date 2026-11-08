; Demo 1 - Core 1: own work, then reads Core 0's result (Section 16.1)
LOAD  R1, [0x01]      ; R1 = 0x05  (same register name as Core 0, different value)
LOAD  R2, [0x02]      ; R2 = 0x03
SLL   R3, R1, R2      ; R3 = 0x05 << 3 = 0x28
XOR   R4, R1, R2      ; R4 = 0x05 ^ 0x03 = 0x06
LOAD  R5, [0x40]      ; R5 = 0x11, written by Core 0 in cycle 3
SUB   R6, R5, R1      ; R6 = 0x11 - 0x05 = 0x0C
STORE R6, [0x41]      ; Mem[0x41] = 0x0C
HALT                  ; Core 1 stops after 8 cycles
