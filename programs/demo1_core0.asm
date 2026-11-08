; Demo 1 - Core 0: computes 12 + 5 and shares it at address 0x40 (Section 16.1)
LOAD  R1, [0x00]      ; R1 = 0x0C (12)
LOAD  R2, [0x01]      ; R2 = 0x05 (5)
ADD   R3, R1, R2      ; R3 = 0x11 (17)
STORE R3, [0x40]      ; Mem[0x40] = 0x11  -> visible to Core 1 from the next cycle
HALT                  ; Core 0 stops after 5 cycles
