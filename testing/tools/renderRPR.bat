@echo off

set PATH=%MAYA_BIN%;%PATH%
set MAYA_RENDER_DESC_PATH=C:\Program Files\AMD\RadeonProRenderPlugins\Maya\renderDesc;%MAYA_RENDER_DESC_PATH%

set CMD=Render -r FireRender -rd %2 -of jpg -im %3 "%1"
echo %CMD%
%CMD%


