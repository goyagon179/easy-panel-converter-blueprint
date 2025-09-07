@echo off
REM Docker Compose to EasyPanel Converter - Windows Batch File
REM Usage: convert.bat input_file [output_file] [project_name]

if "%1"=="" (
    echo Usage: convert.bat input_file [output_file] [project_name]
    echo Example: convert.bat docker-compose.yml schema.json my-project
    exit /b 1
)

set INPUT_FILE=%1
set OUTPUT_FILE=%2
set PROJECT_NAME=%3

if "%OUTPUT_FILE"=="" set OUTPUT_FILE=schema.json
if "%PROJECT_NAME"=="" set PROJECT_NAME=my-project

echo Converting %INPUT_FILE% to EasyPanel schema...
echo Project: %PROJECT_NAME%
echo Output: %OUTPUT_FILE%

REM Try different Python commands
python docker-compose-to-easypanel-converter.py -i "%INPUT_FILE%" -o "%OUTPUT_FILE%" -p "%PROJECT_NAME%" 2>nul
if %errorlevel% equ 0 goto :success

python3 docker-compose-to-easypanel-converter.py -i "%INPUT_FILE%" -o "%OUTPUT_FILE%" -p "%PROJECT_NAME%" 2>nul
if %errorlevel% equ 0 goto :success

py docker-compose-to-easypanel-converter.py -i "%INPUT_FILE%" -o "%OUTPUT_FILE%" -p "%PROJECT_NAME%" 2>nul
if %errorlevel% equ 0 goto :success

echo Error: Python not found. Please install Python 3.7+ and try again.
exit /b 1

:success
echo Conversion completed successfully!
echo Schema saved to: %OUTPUT_FILE%
