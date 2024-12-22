# Findr Installation Script for Windows
Write-Host @"
 _____ _           _      
|  ___(_)_ __   __| |_ __ 
| |_  | | '_ \ / _` | '__|
|  _| | | | | | (_| | |   
|_|   |_|_| |_|\__,_|_|   

🔍 Interactive File Search Tool
Version: 0.1.0

"@ -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.7+ from Microsoft Store or python.org" -ForegroundColor Red
    exit 1
}

# Check pip installation
try {
    $pipVersion = pip --version
    Write-Host "✅ Found pip: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip not found. Please ensure pip is installed with Python" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
if (-not $?) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\activate
if (-not $?) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if (-not $?) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create launcher script
$launcherPath = "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps\findr.ps1"
$scriptContent = @"
#!/usr/bin/env pwsh
`$findrPath = "$PWD"
Set-Location `$findrPath
.\venv\Scripts\activate
python -m findr.cli
deactivate
"@

Write-Host "📝 Creating launcher script..." -ForegroundColor Yellow
try {
    Set-Content -Path $launcherPath -Value $scriptContent -Force
    Write-Host "✅ Created launcher script at: $launcherPath" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create launcher script" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host @"

✨ Installation Complete!

To use Findr:
1. Open PowerShell or Windows Terminal
2. Type 'findr' and press Enter

Note: You might need to restart your terminal for the changes to take effect.
"@ -ForegroundColor Green
