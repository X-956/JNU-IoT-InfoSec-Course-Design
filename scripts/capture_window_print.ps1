param(
    [string]$ProcessName = "isl",
    [string]$OutPath = "qtenv.png"
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Print {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

$proc = Get-Process -Name $ProcessName -ErrorAction Stop |
        Where-Object { $_.MainWindowHandle -ne 0 } |
        Select-Object -First 1
if (-not $proc) { throw "no window for process $ProcessName" }

[Win32Print]::ShowWindow($proc.MainWindowHandle, 3) | Out-Null
Start-Sleep -Milliseconds 800
$proc.Refresh()

$rect = New-Object Win32Print+RECT
[Win32Print]::GetWindowRect($proc.MainWindowHandle, [ref]$rect) | Out-Null
$w = $rect.Right - $rect.Left
$h = $rect.Bottom - $rect.Top
if ($w -le 0 -or $h -le 0) { throw "bad window size ${w}x${h}" }

$bmp = New-Object System.Drawing.Bitmap $w, $h
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [Win32Print]::PrintWindow($proc.MainWindowHandle, $hdc, 2)
$g.ReleaseHdc($hdc)
$g.Dispose()

$dir = Split-Path -Parent $OutPath
if ($dir) { New-Item -ItemType Directory -Force $dir | Out-Null }
$bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output "$OutPath ${w}x${h} printwindow=$ok"
