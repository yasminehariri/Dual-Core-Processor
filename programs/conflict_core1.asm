; Conflict test - Core 1 writes 0x55 to 0x50 in the same cycle as Core 0
LI R1, 0x55
STORE R1, [0x50]
HALT
