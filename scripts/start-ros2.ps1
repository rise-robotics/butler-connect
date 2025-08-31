# Starts Butler Connect with a sourced ROS 2 environment in PowerShell
# Usage: run from project root: .\scripts\start-ros2.ps1 [-Distro humble|iron|jazzy] [-DomainId 0] [-UseWSL]

param(
  [ValidateSet('foxy','galactic','humble','iron','jazzy')]
  [string]$Distro = $env:ROS_DISTRO,
  [int]$DomainId = 0,
  [switch]$UseWSL,
  [string]$WslDistro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

function Info($msg){ Write-Host "[Butler] $msg" -ForegroundColor Cyan }
function Warn($msg){ Write-Warning $msg }
function Fail($msg){ Write-Host $msg -ForegroundColor Red; exit 1 }

# Detect Windows ROS 2 install location
function Get-Ros2SetupPath([string]$distro){
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\ros\$distro\x64\local_setup.ps1",
    "C:\Program Files\ros\$distro\x64\local_setup.ps1",
    "C:\dev\ros2_$distro\local_setup.ps1"
  )
  foreach($p in $candidates){ if(Test-Path $p){ return $p } }
  return $null
}

# Optionally run in WSL if requested
if($UseWSL){
  Info "Launching via WSL..."
  $winPath = (Get-Location).Path
  $drive = $winPath.Substring(0,1).ToLower()
  $rest = $winPath.Substring(2) -replace '\\','/'
  $wslPath = "/mnt/$drive/$rest"
  # Ensure the helper script is executable
  wsl -d $WslDistro bash -lc "cd '$wslPath' && chmod +x scripts/start-ros2-wsl.sh"
  # Export domain and invoke helper inside WSL
  wsl -d $WslDistro bash -lc "export ROS_DOMAIN_ID=$DomainId; cd '$wslPath' && ./scripts/start-ros2-wsl.sh '$Distro' '$wslPath'"
  exit $LASTEXITCODE
}

if(-not $Distro){ Warn "ROS_DISTRO not set; defaulting to 'humble'"; $Distro='humble' }
$setup = Get-Ros2SetupPath $Distro
if(-not $setup){
  Fail "ROS 2 $Distro not found. Install ROS 2 for Windows or run with -UseWSL."
}

Info "Sourcing ROS 2 $Distro from: $setup"
. $setup

# Configure DDS domain if provided
$env:ROS_DOMAIN_ID = "$DomainId"
Info "ROS_DOMAIN_ID=$env:ROS_DOMAIN_ID"

# Ensure venv
if(-not (Test-Path .\venv\Scripts\Activate.ps1)){
  Info "Creating Python venv..."
  python -m venv venv
}
. .\venv\Scripts\Activate.ps1

# Install deps
Info "Installing Python requirements..."
pip install --disable-pip-version-check -q -r requirements.txt

# Run app
$env:PYTHONUNBUFFERED='1'
Info "Starting Butler Connect (ROS 2 mode)..."
python .\src\main.py
