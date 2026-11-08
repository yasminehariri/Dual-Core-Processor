; Conflict test - Core 0 writes 0xAA to 0x50 in the same cycle as Core 1 (Core 0 must win)
LI R1, 0xAA
STORE R1, [0x50]
HALT
