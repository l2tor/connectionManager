@echo off
set dir=%1
set ip_robot=%2

start /b python %dir%/underworlds/bin/underworlded foreground >NUL
timeout /t 3

if "%3" == "" (
start /b python %dir%/connectionManager/tablet/server.py
)

if NOT "%3" == "" (
start /b python %dir%/connectionManager/tablet/server.py --ethernet
)

echo %dir%
echo %ip_robot%

timeout /t 2

start /b python %dir%/OutputManager/app/scripts/outputmanager.py -r %ip_robot% -s 127.0.0.1 >NUL
timeout /t 2

cd %dir%/InteractionManager/interactionmanager/src > NUL
start /b python interaction_manager.py 
cd ../../../..
timeout /t 2

start "" "c:/Program Files (x86)/Google/Chrome/Application/chrome.exe" --allow-file-access-from-files file:%dir%/TabletGame/scene.html
timeout /t 2

rem cd %dir%/WoZControlPanel/WoZControl/bin/Release
rem start /b WoZControl
rem timeout /t 2
cd ../../../../..

timeout /t 2

set /p DUMMY=Press ENTER to terminate everything

:: Kill all python instances. We guess we are the only ones to use python
setlocal EnableDelayedExpansion

for /f "tokens=1" %%a in ('wmic PROCESS where "Name='python.exe'" get ProcessID ^| findstr [0-9]') do (
	tskill %%a
)

for /f "tokens=1" %%a in ('wmic PROCESS where "Name='chrome.exe'" get ProcessID ^| findstr [0-9]') do (
	tskill %%a
)

for /f "tokens=1" %%a in ('wmic PROCESS where "Name='WoZControl.exe'" get ProcessID ^| findstr [0-9]') do (
	tskill %%a
)

endlocal

