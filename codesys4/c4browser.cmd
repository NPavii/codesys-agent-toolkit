@echo off
echo %* > "%~dp0last_url.txt"
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --proxy-server="127.0.0.1:8791" --proxy-bypass-list="<-loopback>" --user-data-dir="%TEMP%\c4-proxy-profile" --new-window "%~1"
