# =============================================================================================
# Install Spice and the VSCode Extension then run VSCode.
#
# Running conditions:
# - Python path should be already declared in terminal env
# =============================================================================================

$SpiceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VscodeDir = Join-Path $SpiceDir "spice-vscode"

Write-Host "Installing Spice (python setup.py install)..." -ForegroundColor Yellow
Set-Location $SpiceDir

python spice-lang/setup.py install

Write-Host "Spice installed" -ForegroundColor Green

# ----------------------------------
# Build & install VSCode extension
# ----------------------------------
Write-Host "Building VSCode extension..." -ForegroundColor Yellow
Set-Location $VscodeDir

npm install
npm run compile

Write-Host "Packaging extension..." -ForegroundColor Yellow
npx vsce package

$Vsix = Get-ChildItem *.vsix | Select-Object -First 1

Write-Host "Installing extension..." -ForegroundColor Yellow
code --install-extension $Vsix --force

# ----------------------------------
# Launch VSCode inside Spice/
# ----------------------------------
Write-Host "Opening VSCode in Spice/" -ForegroundColor Cyan

Set-Location $SpiceDir

code . `
    --extensionDevelopmentPath="$VscodeDir" `
    --disable-extensions
