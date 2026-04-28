@echo off
echo Criando atalho na Area de Trabalho...

set EXE_PATH=%~dp0dist\GMDataCore_Estoque.exe
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\GMDataCore Estoque.lnk

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $s  = $ws.CreateShortcut('%SHORTCUT%'); ^
   $s.TargetPath   = '%EXE_PATH%'; ^
   $s.WorkingDirectory = '%~dp0dist'; ^
   $s.Description  = 'GM DataCore - Controle de Estoque Monte Sinai'; ^
   $s.Save()"

if exist "%SHORTCUT%" (
    echo Atalho criado em: %SHORTCUT%
) else (
    echo ERRO: atalho nao foi criado.
)
pause
