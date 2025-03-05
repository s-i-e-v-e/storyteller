@echo off
setlocal

REM Get the absolute path of the script
for %%a in ("%~f0") do set "script_path=%%~fa"

REM Get the parent directory
for %%a in ("%script_path%\..") do set "parent_dir=%%~fa"

REM Construct the full path to the app.py file
set "app_py=%parent_dir%\src\storyteller\app.py"

REM Run the uv command
uv run --project "%parent_dir%" "%app_py%" %*

endlocal