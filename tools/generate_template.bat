set MAYA_SCRIPT_PATH=%cd%;%MAYA_SCRIPT_PATH%

"C:\Program Files\Autodesk\Maya2018\bin\maya.exe" -command "source generate_template.mel; evalDeferred -lp (makeCommon(\"C:\\Arnold2RPR\\tools\\arnold.ma\"));"