@echo off
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.
echo Installing PDF packages...
pip install arabic-reshaper python-bidi xhtml2pdf openpyxl
echo.
echo Installation complete!
pause
