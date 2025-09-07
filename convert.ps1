# Docker Compose to EasyPanel Converter - PowerShell Script
# Usage: .\convert.ps1 -InputFile docker-compose.yml [-OutputFile schema.json] [-ProjectName my-project]

param(
    [Parameter(Mandatory=$true)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputFile = "schema.json",
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectName = "my-project"
)

Write-Host "Docker Compose to EasyPanel Converter" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Input File: $InputFile" -ForegroundColor Yellow
Write-Host "Output File: $OutputFile" -ForegroundColor Yellow
Write-Host "Project Name: $ProjectName" -ForegroundColor Yellow
Write-Host ""

# Check if input file exists
if (-not (Test-Path $InputFile)) {
    Write-Error "Input file '$InputFile' not found!"
    exit 1
}

# Try different Python commands
$pythonCommands = @("python", "python3", "py")

foreach ($cmd in $pythonCommands) {
    try {
        Write-Host "Trying $cmd..." -ForegroundColor Cyan
        & $cmd docker-compose-to-easypanel-converter.py -i $InputFile -o $OutputFile -p $ProjectName
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Conversion completed successfully!" -ForegroundColor Green
            Write-Host "Schema saved to: $OutputFile" -ForegroundColor Green
            exit 0
        }
    }
    catch {
        Write-Host "❌ $cmd failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Error "Python not found! Please install Python 3.7+ and try again."
Write-Host ""
Write-Host "You can install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
exit 1
