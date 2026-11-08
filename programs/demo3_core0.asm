; Demo 3 - Core 0: adds the first half (1..8), shares it, raises the flag
LOAD R1, [0x00]       ; R1 = 1
LOAD R2, [0x01]       ; R2 = 2
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x02]       ; R2 = 3
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x03]       ; R2 = 4
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x04]       ; R2 = 5
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x05]       ; R2 = 6
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x06]       ; R2 = 7
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x07]       ; R2 = 8
ADD  R1, R1, R2       ; running sum
STORE R1, [0x80]      ; partial sum 36 (0x24)
LI   R3, 1
STORE R3, [0xF0]      ; flag: partial sum ready
HALT                  ; 19 cycles
