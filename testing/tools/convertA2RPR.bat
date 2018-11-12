@echo off

set CWD=%~dp0

set PATH=%MAYA_BIN%;%PATH%
set MAYA_SCRIPT_PATH=%CWD%;%CWD%\..\..\;%MAYA_SCRIPT_PATH%

set CMD=maya.exe -command "source convertSceneFile.mel; evalDeferred -lp (convertSceneFile(\"%1\", \"%2\"));"
echo %CMD%
%CMD%



