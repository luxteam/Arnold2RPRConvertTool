@echo off

set CWD1=%~dp0
set CWD=%CWD1:\=\\%

set MAYA_BIN=C:\Program Files\Autodesk\Maya2017\bin

set TESTS=^
                Subsurface_Test.ma^
		



FOR %%A IN (%TESTS%) DO (
call tools\convertA2RPR.bat %CWD%scenesArnold\\%%A %CWD%scenesRPR\\%%A
call tools\renderArnold.bat %CWD%scenesArnold\\%%A %CWD%output\\Arnold %%A
call tools\renderRPR.bat %CWD%scenesRPR\\%%A %CWD%output\\RPR %%A
)
