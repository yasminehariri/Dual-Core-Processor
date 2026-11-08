@echo off
REM ==========================================================================
REM run_all.bat - compiles and runs every testbench in tb\ with Questa.
REM Run it from the repo root in a Questa-enabled terminal (or the Questa
REM Transcript:  do run_all.do ). Exits with 1 if any testbench fails.
REM ==========================================================================
setlocal enabledelayedexpansion
if not exist work vlib work >nul
if not exist logs mkdir logs
set SRC=
for %%S in (src\*.v) do set SRC=!SRC! %%S
set FAIL=0
set COUNT=0
echo.
for %%F in (tb\tb_*.v) do (
  set NAME=%%~nF
  if /I not "!NAME!"=="tb_template" (
    set /a COUNT+=1
    vlog -quiet -lint !SRC! %%F > logs\!NAME!_compile.log 2>&1
    if errorlevel 1 (
      echo   !NAME!   COMPILE ERROR  ^(see logs\!NAME!_compile.log^)
      set FAIL=1
    ) else (
      vsim -c !NAME! -do "run -all; quit -f" > logs\!NAME!.log 2>&1
      findstr /C:"ALL PASS" logs\!NAME!.log >nul
      if errorlevel 1 (
        echo   !NAME!   FAILED  ^(see logs\!NAME!.log^)
        set FAIL=1
      ) else (
        echo   !NAME!   ALL PASS
      )
    )
  )
)
echo.
if !FAIL!==1 (
  echo SOME TESTBENCHES FAILED
  exit /b 1
)
echo ALL !COUNT! TESTBENCHES PASSED
exit /b 0
