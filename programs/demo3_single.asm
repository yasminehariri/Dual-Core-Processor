; Demo 3 - single core: adds Mem[0x00..0x0F] = 1..16 alone (Section 16.3)
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
LOAD R2, [0x08]       ; R2 = 9
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x09]       ; R2 = 10
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0A]       ; R2 = 11
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0B]       ; R2 = 12
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0C]       ; R2 = 13
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0D]       ; R2 = 14
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0E]       ; R2 = 15
ADD  R1, R1, R2       ; running sum
LOAD R2, [0x0F]       ; R2 = 16
ADD  R1, R1, R2       ; running sum
STORE R1, [0x82]      ; Mem[0x82] = 136 (0x88)
HALT                  ; 33 cycles
