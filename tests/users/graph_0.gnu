set term postscript landscape monochrom  
#set term x11 
set out "graph_0.ps"
set grid
set title "File:piston.frd"
set xlabel " nr "
set ylabel " STEP "
plot "graph_0.out" using 1:2 title 'val1' with linespoints, "graph_0.out" using 1:3 title 'val2' with linespoints, "graph_0.out" using 1:4 title 'val3' with linespoints

