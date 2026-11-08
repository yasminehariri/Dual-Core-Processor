; Loop test (ADDI + BNE): 5+4+3+2+1 = 15 (Section 16.4)
      LI   R1, 5        ; counter
      CLR  R2           ; sum = 0
loop: ADD  R2, R2, R1   ; sum += counter
      ADDI R1, R1, -1   ; counter--
      BNE  R1, R0, loop ; repeat until counter is 0
      STORE R2, [0x90]  ; Mem[0x90] = 0x0F
      HALT              ; 19 cycles
