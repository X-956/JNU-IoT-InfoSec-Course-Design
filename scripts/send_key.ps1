param([string]$ProcessName = "isl", [int]$KeyCode = 0x75)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Key2 {
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@
$proc = Get-Process -Name $ProcessName -ErrorAction Stop |
        Where-Object { $_.MainWindowHandle -ne 0 } |
        Select-Object -First 1
if (-not $proc) { throw "no window" }
$h = $proc.MainWindowHandle
[Win32Key2]::PostMessage($h, 0x0100, [IntPtr]$KeyCode, [IntPtr]0) | Out-Null
Start-Sleep -Milliseconds 100
[Win32Key2]::PostMessage($h, 0x0101, [IntPtr]$KeyCode, [IntPtr]0) | Out-Null
Write-Output ("key 0x{0:X} posted to {1}" -f $KeyCode, $proc.Id)
