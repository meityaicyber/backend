@echo off
echo Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat
echo Installing dependencies offline...
pip install --no-index --find-links=vendor -r requirements.txt
echo Installation complete.
