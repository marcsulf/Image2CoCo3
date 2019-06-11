@echo off
decb dskini %~n1.DSK
decb copy %1 %~n1.DSK,%~nx1 -0 -a
decb copy %~n1" 1.BIN" %~n1.DSK,%~n1" 1.BIN" -2
decb copy %~n1" 2.BIN" %~n1.DSK,%~n1" 2.BIN" -2
decb copy %~n1" 3.BIN" %~n1.DSK,%~n1" 3.BIN" -2
decb copy %~n1" 4.BIN" %~n1.DSK,%~n1" 4.BIN" -2
decb dir %~n1.DSK
