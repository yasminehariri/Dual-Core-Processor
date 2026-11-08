; Demo 3 - Core 1: adds the second half (9..16), waits for Core 0, combines
LOAD R1, [0x08]       ; R1 = 9
LOAD R2, [0x09]       ; R2 = 10
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0A]       ; R2 = 11
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0B]       ; R2 = 12
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0C]       ; R2 = 13
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0D]       ; R2 = 14
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0E]       ; R2 = 15
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
LOAD R2, [0x0F]       ; R2 = 16
ADD  R1, R1, R2       ; running sum (ends at 100 = 0x64)
wait: LOAD R3, [0xF0] ; flag from Core 0
BEQ  R3, R0, wait     ; not ready yet: check again
LOAD R2, [0x80]       ; Core 0's partial sum
ADD  R1, R1, R2       ; 100 + 36 = 136
STORE R1, [0x82]      ; Mem[0x82] = 0x88
HALT                  ; 25 cycles
