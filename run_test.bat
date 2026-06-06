@echo off
cd /d e:\solo\项目\lym-00008
echo Running test_user_bugs.py...
"C:\Users\Huwenjie\AppData\Local\Microsoft\WindowsApps\python.exe" test_user_bugs.py > test_user_bugs_output.txt 2>&1
echo Exit code: %ERRORLEVEL%
type test_user_bugs_output.txt
