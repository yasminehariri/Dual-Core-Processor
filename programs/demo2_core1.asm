; Demo 2 - Core 1: waits on the flag instead of trusting timing (Section 16.2)
wait: LOAD R1, [0xF0] ; read the flag
      BEQ  R1, R0, wait ; still 0? check again (R0 is 0 by convention)
      LOAD R2, [0x80] ; R2 = 42, Core 0's result
      LI   R3, 2
      SUB  R4, R2, R3 ; R4 = 40 (0x28)
      STORE R4, [0x81]; Mem[0x81] = 0x28
      HALT            ; Core 1 stops after 13 cycles
