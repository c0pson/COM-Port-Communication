$dir = Get-Location

Start-Process powershell -WindowStyle Hidden -WorkingDirectory $dir -ArgumentList "-NoExit", "-Command", "& .\.venv\bin\python.exe src\main.py"
Start-Process powershell -WindowStyle Hidden -WorkingDirectory $dir -ArgumentList "-NoExit", "-Command", "& .\.venv\bin\python.exe src\main.py"
