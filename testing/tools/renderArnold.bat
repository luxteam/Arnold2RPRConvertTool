@echo off

set PATH=%MAYA_BIN%;%PATH%

set CMD=Render -r arnold -rd %2 -of jpg -im %3 "%1"
echo %CMD%
%CMD%

