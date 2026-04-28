param(
    [switch]$Clean,
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppName = "SOM Quality Checker"
$EntryPoint = Join-Path $ProjectRoot "main.py"
$LogoPath = Join-Path $ProjectRoot "logo.png"
$IconPath = Join-Path $ProjectRoot "build\logo.ico"
$DistPath = Join-Path $ProjectRoot "dist"
$BuildPath = Join-Path $ProjectRoot "build"
$SpecPath = Join-Path $ProjectRoot "$AppName.spec"
$PackagePath = Join-Path $ProjectRoot "som_analyzer\src"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install uv or run this script from an environment where uv is available."
}

if (-not (Test-Path -LiteralPath $EntryPoint)) {
    throw "Entry point not found: $EntryPoint"
}

if (-not (Test-Path -LiteralPath $LogoPath)) {
    throw "Logo not found: $LogoPath"
}

function Convert-PngToIco {
    param(
        [Parameter(Mandatory = $true)][string]$PngPath,
        [Parameter(Mandatory = $true)][string]$IcoPath
    )

    Add-Type -AssemblyName System.Drawing

    $IconDir = Split-Path -Parent $IcoPath
    if (-not (Test-Path -LiteralPath $IconDir)) {
        New-Item -ItemType Directory -Path $IconDir | Out-Null
    }

    $Sizes = @(256, 128, 64, 48, 32, 16)
    $Images = New-Object System.Collections.Generic.List[object]
    $Source = [System.Drawing.Image]::FromFile($PngPath)

    try {
        foreach ($Size in $Sizes) {
            $Bitmap = New-Object System.Drawing.Bitmap $Size, $Size
            $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
            try {
                $Graphics.Clear([System.Drawing.Color]::Transparent)
                $Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                $Graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
                $Graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality

                $Scale = [Math]::Min($Size / $Source.Width, $Size / $Source.Height)
                $Width = [int]($Source.Width * $Scale)
                $Height = [int]($Source.Height * $Scale)
                $X = [int](($Size - $Width) / 2)
                $Y = [int](($Size - $Height) / 2)
                $Graphics.DrawImage($Source, $X, $Y, $Width, $Height)

                $Stream = New-Object System.IO.MemoryStream
                $Bitmap.Save($Stream, [System.Drawing.Imaging.ImageFormat]::Png)
                $Images.Add([pscustomobject]@{
                    Size = $Size
                    Bytes = $Stream.ToArray()
                })
            }
            finally {
                $Graphics.Dispose()
                $Bitmap.Dispose()
            }
        }
    }
    finally {
        $Source.Dispose()
    }

    $Writer = New-Object System.IO.BinaryWriter([System.IO.File]::Create($IcoPath))
    try {
        $Writer.Write([UInt16]0)
        $Writer.Write([UInt16]1)
        $Writer.Write([UInt16]$Images.Count)

        $Offset = 6 + (16 * $Images.Count)
        foreach ($Image in $Images) {
            $Dimension = if ($Image.Size -eq 256) { 0 } else { $Image.Size }
            $Writer.Write([Byte]$Dimension)
            $Writer.Write([Byte]$Dimension)
            $Writer.Write([Byte]0)
            $Writer.Write([Byte]0)
            $Writer.Write([UInt16]1)
            $Writer.Write([UInt16]32)
            $Writer.Write([UInt32]$Image.Bytes.Length)
            $Writer.Write([UInt32]$Offset)
            $Offset += $Image.Bytes.Length
        }

        foreach ($Image in $Images) {
            $Writer.Write($Image.Bytes)
        }
    }
    finally {
        $Writer.Dispose()
    }
}

if ($Clean) {
    foreach ($Path in @($DistPath, $BuildPath, $SpecPath)) {
        if (Test-Path -LiteralPath $Path) {
            Remove-Item -LiteralPath $Path -Recurse -Force
        }
    }
}

$Mode = if ($OneDir) { "--onedir" } else { "--onefile" }
$AddData = "$LogoPath;."

Convert-PngToIco -PngPath $LogoPath -IcoPath $IconPath

$Arguments = @(
    "run",
    "--with", "pyinstaller",
    "pyinstaller",
    $Mode,
    "--noconfirm",
    "--windowed",
    "--name", $AppName,
    "--paths", $PackagePath,
    "--collect-submodules", "som_analyzer",
    "--hidden-import", "som_analyzer.gui.app",
    "--add-data", $AddData,
    "--icon", $IconPath,
    $EntryPoint
)

Write-Host "Building $AppName..."
Write-Host "Project: $ProjectRoot"
Write-Host "Mode: $Mode"

Push-Location $ProjectRoot
try {
    & uv @Arguments
}
finally {
    Pop-Location
}

$ExpectedExe = if ($OneDir) {
    Join-Path $DistPath "$AppName\$AppName.exe"
} else {
    Join-Path $DistPath "$AppName.exe"
}

if (-not (Test-Path -LiteralPath $ExpectedExe)) {
    throw "Build finished, but executable was not found at: $ExpectedExe"
}

Write-Host "Build complete:"
Write-Host $ExpectedExe
