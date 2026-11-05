@echo off
rem Только перехватываем URL с InitToken, НЕ открывая браузер (токен одноразовый)
echo %* > "%~dp0last_url.txt"
