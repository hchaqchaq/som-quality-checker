param(
    [switch]$Clean,
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppName = "Quality Checker"
$EntryPoint = Join-Path $ProjectRoot "main.py"
$LogoPath = Join-Path $ProjectRoot "logo.png"
$DistPath = Join-Path $ProjectRoot "dist"
$BuildPath = Join-Path $ProjectRoot "build"
$SpecPath = Join-Path $ProjectRoot "$AppName.spec"
$PackagePath = Join-Path $ProjectRoot "quality_checker\src"

if (-not (Get-Command uv -ErrorAction SilentlyContinue))
{
    throw "uv is required. Install uv or run this script from an environment where uv is available."
}

if (-not (Test-Path -LiteralPath $EntryPoint))
{
    throw "Entry point not found: $EntryPoint"
}

if (-not (Test-Path -LiteralPath $LogoPath))
{
    throw "Logo not found: $LogoPath"
}

if ($Clean)
{
    foreach ($Path in @($DistPath, $BuildPath, $SpecPath))
    {
        if (Test-Path -LiteralPath $Path)
        {
            Remove-Item -LiteralPath $Path -Recurse -Force
        }
    }
}

$Mode = if ($OneDir)
{
    "--onedir"
}
else
{
    "--onefile"
}
$AddData = "$LogoPath;."

$Arguments = @(
    "run",
    "--with", "pyinstaller",
    "--with", "pillow",
    "pyinstaller",
    $Mode,
    "--noconfirm",
    "--windowed",
    "--name", $AppName,
    "--paths", $PackagePath,
    "--collect-submodules", "quality_checker",
    "--hidden-import", "quality_checker.gui.app",
    "--add-data", $AddData,
    "--icon", $LogoPath,
    $EntryPoint
)

Write-Host "Building $AppName..."
Write-Host "Project: $ProjectRoot"
Write-Host "Mode: $Mode"

Push-Location $ProjectRoot
try
{
    & uv @Arguments
}
finally
{
    Pop-Location
}

$ExpectedExe = if ($OneDir)
{
    Join-Path $DistPath "$AppName\$AppName.exe"
}
else
{
    Join-Path $DistPath "$AppName.exe"
}

if (-not (Test-Path -LiteralPath $ExpectedExe))
{
    throw "Build finished, but executable was not found at: $ExpectedExe"
}

Write-Host "Build complete:"
Write-Host $ExpectedExe
