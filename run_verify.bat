@echo off
cd /d e:\solo\项目\lym-00008
echo Starting verification at %date% %time% > verify_fix_log.txt
echo. >> verify_fix_log.txt

where python >> verify_fix_log.txt 2>&1
echo. >> verify_fix_log.txt

echo Trying to run Python... >> verify_fix_log.txt

for %%P in (
    "C:\Users\Huwenjie\AppData\Local\Microsoft\WindowsApps\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
    "C:\Python38\python.exe"
    "C:\Program Files\Python310\python.exe"
    "C:\Program Files\Python39\python.exe"
    python
    py
) do (
    if exist %%~P (
        echo Found Python at %%~P >> verify_fix_log.txt
        echo. >> verify_fix_log.txt
        echo Running verify_fix.py with %%~P... >> verify_fix_log.txt
        %%~P verify_fix.py >> verify_fix_log.txt 2>&1
        set EXITCODE=%ERRORLEVEL%
        echo. >> verify_fix_log.txt
        echo Exit code: %EXITCODE% >> verify_fix_log.txt
        goto :done
    )
)

echo No Python found! >> verify_fix_log.txt
set EXITCODE=9009

:done
echo. >> verify_fix_log.txt
echo Finished at %date% %time% >> verify_fix_log.txt

echo Exit code: %EXITCODE%
type verify_fix_log.txt
