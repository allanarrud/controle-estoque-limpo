@echo off
echo ============================================
echo  GM DataCore — Build de Executaveis
echo ============================================
echo.

echo Limpando builds antigos...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del GMDataCore_Estoque.spec 2>nul
echo.

echo [1/3] Gerando icone a partir da logo...
python gerar_icone.py
if not exist assets\icon.ico (
    echo  ERRO: icone nao foi gerado. Verifique assets\logo_montesinai.png
    pause
    exit /b 1
)
echo.

echo [2/3] Gerando GMDataCore_Estoque.exe ...
pyinstaller ^
  --onefile ^
  --noconsole ^
  --name GMDataCore_Estoque ^
  --icon=assets\icon.ico ^
  --add-data "assets;assets" ^
  --collect-all PIL ^
  launcher_wrapper.py

echo.
if not exist dist\GMDataCore_Estoque.exe (
    echo  BUILD FALHOU. Verifique os erros acima.
    pause
    exit /b 1
)

echo  BUILD OK: dist\GMDataCore_Estoque.exe
echo.

echo [3/3] Criando atalho na Area de Trabalho...
set EXE_PATH=%~dp0dist\GMDataCore_Estoque.exe

powershell -NoProfile -Command ^
  "$desktop = [Environment]::GetFolderPath('Desktop');" ^
  "$lnk = Join-Path $desktop 'GMDataCore_Estoque.lnk';" ^
  "$exe = '%EXE_PATH%';" ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$s = $ws.CreateShortcut($lnk);" ^
  "$s.TargetPath = $exe;" ^
  "$s.WorkingDirectory = Split-Path $exe;" ^
  "$s.Description = 'GM DataCore - Controle de Estoque Monte Sinai';" ^
  "$s.IconLocation = $exe;" ^
  "$s.Save();" ^
  "Write-Output $lnk"

powershell -NoProfile -Command "if (Test-Path (Join-Path ([Environment]::GetFolderPath('Desktop')) 'GMDataCore_Estoque.lnk')) { Write-Output 'OK' } else { Write-Output 'FAIL' }" > %TEMP%\atalho_check.txt
set /p ATALHO_STATUS=<%TEMP%\atalho_check.txt
if "%ATALHO_STATUS%"=="OK" (
    echo  ATALHO OK na Area de Trabalho.
) else (
    echo  AVISO: atalho nao foi criado.
)

echo.
echo ============================================
echo  Tudo pronto! Clique em GMDataCore_Estoque
echo  na sua Area de Trabalho para abrir o app.
echo ============================================
if "%TERM_PROGRAM%"=="" if "%WT_SESSION%"=="" pause
