# WikiRace setup
#
# The game deliberately has no third-party dependencies - it's written against
# the Python standard library only, so there is nothing to pip install. The one
# thing a fresh machine can be missing is Python itself, and that's what this
# script sorts out.

# Deliberately not 'Stop': probing interpreters means running commands that are
# expected to fail, and in Windows PowerShell a native command's stderr becomes
# an ErrorRecord - which under 'Stop' would abort the very checks we're making.
$ErrorActionPreference = 'Continue'
$MinVersion = [Version]'3.8'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Say     ($m) { Write-Host "  $m" }
function SayOk   ($m) { Write-Host "  $m" -ForegroundColor Green }
function SayWarn ($m) { Write-Host "  $m" -ForegroundColor Yellow }
function SayBad  ($m) { Write-Host "  $m" -ForegroundColor Red }

function Update-SessionPath {
    # A fresh install writes PATH to the registry, but this process still has
    # the old copy - pull it back in so we can find what we just installed.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($machine, $user) | Where-Object { $_ }) -join ';'
}

function Test-Interpreter($exe, $prefix) {
    # Returns the version, or $null if this isn't a Python we can use.
    # Notably this rejects the Microsoft Store placeholder that ships on clean
    # Windows installs: it's named python.exe but only opens the Store.
    try {
        $callArgs = @()
        if ($prefix) { $callArgs += $prefix }
        $callArgs += @('-c', 'import sys; print("%d.%d" % sys.version_info[:2])')
        $out = & $exe @callArgs 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $out) { return $null }
        $version = [Version]($out | Select-Object -First 1).Trim()
        if ($version -ge $MinVersion) { return $version }
    } catch { }
    return $null
}

function Find-Python {
    foreach ($c in @(
        @{ exe = 'py';      prefix = '-3'  },
        @{ exe = 'python';  prefix = $null },
        @{ exe = 'python3'; prefix = $null }
    )) {
        if (Get-Command $c.exe -ErrorAction SilentlyContinue) {
            $v = Test-Interpreter $c.exe $c.prefix
            if ($v) {
                return [pscustomobject]@{ Exe = $c.exe; Prefix = $c.prefix; Version = $v }
            }
        }
    }
    # Not on PATH yet? Look where per-user installs actually land.
    foreach ($glob in @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe"
    )) {
        $found = Get-ChildItem $glob -ErrorAction SilentlyContinue |
                 Sort-Object FullName -Descending
        foreach ($p in $found) {
            $v = Test-Interpreter $p.FullName $null
            if ($v) {
                return [pscustomobject]@{ Exe = $p.FullName; Prefix = $null; Version = $v }
            }
        }
    }
    return $null
}

function Install-WithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        SayWarn "winget isn't available on this machine."
        return $false
    }
    foreach ($id in @('Python.Python.3.13', 'Python.Python.3.12')) {
        # Per-user first: it needs no admin rights. Fall back to the default
        # scope if the package won't install that way.
        foreach ($scoped in @($true, $false)) {
            Say "Installing $id via winget$(if ($scoped) { ' (per-user)' })..."
            $a = @('install', '--id', $id, '--exact', '--source', 'winget',
                   '--accept-package-agreements', '--accept-source-agreements',
                   '--disable-interactivity')
            if ($scoped) { $a += @('--scope', 'user') }
            & winget @a | Out-Host
            if ($LASTEXITCODE -eq 0) { return $true }
            SayWarn "winget exited with $LASTEXITCODE."
        }
    }
    return $false
}

function Install-FromPythonOrg {
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'arm64' } else { 'amd64' }
    $ver  = '3.12.10'
    $url  = "https://www.python.org/ftp/python/$ver/python-$ver-$arch.exe"
    $dest = Join-Path $env:TEMP "python-$ver-$arch.exe"

    Say "Downloading Python $ver ($arch) from python.org..."
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -ErrorAction Stop

    Say "Running the installer - per-user, and adding Python to PATH..."
    $proc = Start-Process -FilePath $dest -Wait -PassThru -ArgumentList @(
        '/quiet', 'InstallAllUsers=0', 'PrependPath=1',
        'Include_launcher=1', 'Include_test=0', 'Include_pip=1'
    )
    Remove-Item $dest -Force -ErrorAction SilentlyContinue
    if ($proc.ExitCode -ne 0) {
        SayWarn "The installer exited with $($proc.ExitCode)."
        return $false
    }
    return $true
}

function Test-GameRuns($py) {
    # Prove this interpreter can actually run the game, rather than just
    # reporting a version - a stripped-down Python would fail here.
    $script = Join-Path $Here 'wikirace.py'
    if (-not (Test-Path $script)) {
        SayWarn "wikirace.py isn't next to this script, so I can't verify it."
        return $true
    }
    $callArgs = @()
    if ($py.Prefix) { $callArgs += $py.Prefix }
    $callArgs += @('-c', @'
import sys, py_compile
for m in ("socket","json","threading","hashlib","uuid","webbrowser","struct","http.server"):
    __import__(m)
py_compile.compile(sys.argv[1], doraise=True)
print("ok")
'@, $script)
    # No stderr redirect here: any traceback should land in front of the user,
    # and redirecting a native command's stderr misbehaves in Windows PowerShell.
    $out = & $py.Exe @callArgs
    if ($LASTEXITCODE -eq 0 -and ($out -join '') -match 'ok') { return $true }
    SayBad "That Python couldn't run the game (details above)."
    return $false
}

# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "  WikiRace setup" -ForegroundColor Cyan
Write-Host "  --------------"
Say "The game needs no extra packages - it uses only Python's standard"
Say "library. This just makes sure Python itself is installed."
Write-Host ""

$py = Find-Python
if ($py) {
    SayOk "Found Python $($py.Version) already installed."
} else {
    Say "No Python $MinVersion or newer found. Installing it now."
    Write-Host ""
    $installed = Install-WithWinget
    if (-not $installed) {
        SayWarn "Trying a direct download from python.org instead."
        try { $installed = Install-FromPythonOrg }
        catch { SayBad $_.Exception.Message; $installed = $false }
    }
    Write-Host ""
    Update-SessionPath
    $py = Find-Python
}

if (-not $py) {
    SayBad "Couldn't get Python installed automatically."
    Write-Host ""
    Say "Install it by hand from https://www.python.org/downloads/"
    Say "On the first screen, tick 'Add python.exe to PATH'."
    Write-Host ""
    exit 1
}

if (-not (Test-GameRuns $py)) {
    Write-Host ""
    exit 1
}

Write-Host ""
SayOk "All set - Python $($py.Version) is ready and the game compiles."
Write-Host ""
Say "Start playing by double-clicking 'Play WikiRace.bat'."
Say "The first run pops a Windows Firewall prompt - allow it on Private"
Say "networks, or the other players won't be able to see you."
Write-Host ""
exit 0
