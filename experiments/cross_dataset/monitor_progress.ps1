$logs = "E:\thard_year\experiments\results\cross_dataset\logs"
$configs = @(
    @{ Name = "isot";  Label = "BERT trained on ISOT";        Weight = 26.8 },
    @{ Name = "liar";  Label = "BERT trained on LIAR";        Weight = 16.0 },
    @{ Name = "mixed"; Label = "BERT trained on ISOT + LIAR"; Weight = 42.8 }
)
$seeds = 3; $epochs = 2
$totalUnits = 0; foreach ($c in $configs) { $totalUnits += $c.Weight * $seeds * $epochs }
$start = Get-Date

function Bar($frac, $width = 40) {
    $f = [double]$frac
    if ($f -lt 0) { $f = 0.0 } elseif ($f -gt 1) { $f = 1.0 }
    $n = [int][math]::Floor($f * $width)
    return "[" + ("#" * $n) + ("-" * ($width - $n)) + "] " + ("{0,5:N1}%" -f ($f * 100))
}

while ($true) {
    Clear-Host
    $doneUnits = 0; $doneSecs = 0; $lines = @()
    foreach ($c in $configs) {
        $f = Join-Path $logs ("bert_" + $c.Name + ".log")
        $ep = @()
        if (Test-Path $f) { $ep = @(Select-String -Path $f -Pattern "seed (\d+) epoch (\d+): val F1 ([\d.]+) \((\d+)s\)") }
        $n = $ep.Count
        foreach ($m in $ep) { $doneSecs += [double]$m.Matches[0].Groups[4].Value }
        $doneUnits += $n * $c.Weight
        $state = if ($n -ge $seeds * $epochs) { "done" } elseif ($n -gt 0 -or (Test-Path $f)) { "running" } else { "waiting" }
        $lines += ("{0,-28} {1}  {2}/{3} epochs  {4}" -f $c.Label, (Bar ($n / ($seeds * $epochs))), $n, ($seeds * $epochs), $state)
        if ($ep.Count -gt 0) {
            $last = $ep[-1].Matches[0].Groups
            $lines += ("{0,-28} last: seed {1} epoch {2}, val F1 {3}, {4}s" -f "", $last[1].Value, $last[2].Value, $last[3].Value, $last[4].Value)
        }
    }
    $overall = $doneUnits / $totalUnits
    Write-Host "BERT cross-dataset experiment" -ForegroundColor Cyan
    Write-Host ("Started monitor: {0}   Now: {1}" -f $start.ToString("HH:mm:ss"), (Get-Date).ToString("HH:mm:ss"))
    Write-Host ""
    $lines | ForEach-Object { Write-Host $_ }
    Write-Host ""
    Write-Host ("OVERALL {0}" -f (Bar $overall)) -ForegroundColor Green
    if ($doneUnits -gt 0 -and $doneSecs -gt 0) {
        $remain = ($totalUnits - $doneUnits) * ($doneSecs / $doneUnits)
        Write-Host ("Estimated time left: {0:N0} min (finish around {1})" -f ($remain / 60), (Get-Date).AddSeconds($remain).ToString("HH:mm"))
    } else {
        Write-Host "Estimated time left: waiting for the first epoch to finish..."
    }
    $gpu = Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue
    if ($gpu) {
        $u = ($gpu.CounterSamples | Group-Object { ($_.InstanceName -split "_engtype_")[1] } | ForEach-Object { ($_.Group | Measure-Object CookedValue -Sum).Sum } | Measure-Object -Maximum).Maximum
        Write-Host ("GPU load (busiest engine): {0:N0}%" -f [math]::Min(100, $u))
    }
    if (Test-Path (Join-Path $logs "bert_done.log")) { Write-Host "`nALL RUNS FINISHED" -ForegroundColor Yellow; break }
    Start-Sleep -Seconds 5
}
