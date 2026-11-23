param([string]$ProcessName = "isl")
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Key {
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@
$proc = Get-Process -Name $ProcessName -ErrorAction Stop |
        Where-Object { $_.MainWindowHandle -ne 0 } |
        Select-Object -First 1
if (-not $proc) { throw "no window" }
$h = $proc.MainWindowHandle
[Win32Key]::PostMessage($h, 0x0100, [IntPtr]0x74, [IntPtr]0) | Out-Null
Start-Sleep -Milliseconds 100
[Win32Key]::PostMessage($h, 0x0101, [IntPtr]0x74, [IntPtr]0) | Out-Null
Write-Output "F5 posted to $($proc.Id)"
