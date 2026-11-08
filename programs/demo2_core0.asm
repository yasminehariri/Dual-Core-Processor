; Demo 2 - Core 0: computes 42, stores it, then raises the flag (Section 16.2)
LI    R1, 25          ; R1 = 25
LI    R2, 17          ; R2 = 17
ADD   R3, R1, R2      ; R3 = 42 (0x2A)
STORE R3, [0x80]      ; shared result
LI    R4, 1
STORE R4, [0xF0]      ; flag: result is ready
HALT                  ; Core 0 stops after 7 cycles
