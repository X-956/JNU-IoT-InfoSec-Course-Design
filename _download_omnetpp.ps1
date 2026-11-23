$ErrorActionPreference = 'Stop'
$url = 'https://ghproxy.net/https://github.com/omnetpp/omnetpp/releases/download/omnetpp-6.4.0/omnetpp-6.4.0-windows-x86_64.7z'
$size = 1209918370
$sha  = '3c0957fe466332bcf441f132ac0fe102986c96699f50fee03abbcafbdc4504ab'
$dir  = 'D:\download\omnetpp-6.4.0'
$n    = 6
New-Item -ItemType Directory -Force $dir | Out-Null

$chunk = [math]::Ceiling($size / $n)
Write-Output "[$(Get-Date -Format HH:mm:ss)] start, size=$size chunk=$chunk parts=$n"

$procs = @()
for ($i = 0; $i -lt $n; $i++) {
    $start = $i * $chunk
    $end   = [math]::Min($start + $chunk - 1, $size - 1)
    $out   = Join-Path $dir ("part{0:D2}.bin" -f $i)
    $args  = @('-L','--fail','--retry','8','--retry-delay','5','--retry-all-errors',
               '--range',"$start-$end",'-o',$out,$url)
    $procs += Start-Process -FilePath 'curl.exe' -ArgumentList $args -PassThru -NoNewWindow
}
$procs | Wait-Process
Write-Output "[$(Get-Date -Format HH:mm:ss)] curl processes finished"

$parts = Get-ChildItem $dir -Filter 'part*.bin' | Sort-Object Name
$sum = ($parts | Measure-Object Length -Sum).Sum
if ($sum -ne $size) {
    Write-Output "SIZE MISMATCH: got $sum expected $size"
    $parts | Select-Object Name,Length
    exit 2
}

$final = Join-Path $dir 'omnetpp-6.4.0-windows-x86_64.7z'
$fs = [System.IO.File]::Open($final, 'Create', 'Write')
try {
    foreach ($p in $parts) {
        $in = [System.IO.File]::OpenRead($p.FullName)
        try { $in.CopyTo($fs) } finally { $in.Dispose() }
    }
} finally { $fs.Dispose() }
Write-Output "[$(Get-Date -Format HH:mm:ss)] concatenated -> $final"

$hash = (Get-FileHash $final -Algorithm SHA256).Hash.ToLower()
Write-Output "sha256=$hash"
if ($hash -ne $sha) { Write-Output 'HASH MISMATCH'; exit 3 }
Write-Output 'DOWNLOAD_OK'
