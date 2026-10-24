@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 goto folder_error
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" uruchom.py
    goto finished
)
py -3 -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 (
    py -3 uruchom.py
    goto finished
)
python -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>&1
if not errorlevel 1 (
    python uruchom.py
    goto finished
)
echo Nie znaleziono dzialajacego Pythona 3.12 lub nowszego.
echo Zainstaluj Python z https://www.python.org/downloads/windows/
echo Zaznacz opcje Add python.exe to PATH i ponownie otworz ten plik.
goto finish_pause
:finished
if errorlevel 1 (
    echo.
    echo Nie udalo sie uruchomic aplikacji. Szczegoly znajduja sie powyzej.
    echo Jesli przeniesiono .venv z innego komputera, zmien nazwe folderu
    echo na .venv-stare i uruchom ten plik ponownie.
)
:finish_pause
popd
echo.
pause
exit /b
:folder_error
echo Nie mozna otworzyc katalogu projektu. Najpierw rozpakuj caly ZIP.
pause
