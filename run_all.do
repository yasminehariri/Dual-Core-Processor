# run_all.do - same as run_all.bat, from inside the Questa window:
#   cd <repo folder>   then   do run_all.do
if {![file exists work]} { vlib work }
file mkdir logs
set src [glob src/*.v]
set fail 0
set count 0
foreach tb [lsort [glob tb/tb_*.v]] {
    set name [file rootname [file tail $tb]]
    if {$name eq "tb_template"} { continue }
    incr count
    if {[catch {eval vlog -quiet -lint $src $tb} err]} {
        echo "  $name   COMPILE ERROR"
        set fail 1
        continue
    }
    transcript file logs/$name.log
    vsim -quiet -onfinish stop $name
    run -all
    quit -sim
    transcript file transcript
    set fh [open logs/$name.log r]; set log [read $fh]; close $fh
    if {[string first "ALL PASS" $log] >= 0} { echo "  $name   ALL PASS" } else { echo "  $name   FAILED (see logs/$name.log)"; set fail 1 }
}
if {$fail} { echo "SOME TESTBENCHES FAILED" } else { echo "ALL $count TESTBENCHES PASSED" }
