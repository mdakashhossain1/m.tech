$logs = "E:\thard_year\experiments\results\cross_dataset\logs"
$epochs = 3
$jobs = @(
    @{ Ds = "liar"; Model = "bilstm";      Label = "LIAR  BiLSTM";      Guess = 25 },
    @{ Ds = "liar"; Model = "bert";        Label = "LIAR  BERT";        Guess = 290 },
    @{ Ds = "liar"; Model = "bert_bilstm"; Label = "LIAR  BERT+BiLSTM"; Guess = 330 },
    @{ Ds = "isot"; Model = "bilstm";      Label = "ISOT  BiLSTM";      Guess = 60 },
    @{ Ds = "isot"; Model = "bert";        Label = "ISOT  BERT";        Guess = 450 },
    @{ Ds = "isot"; Model = "bert_bilstm"; Label = "ISOT  BERT+BiLSTM"; Guess = 520 }
)
$pattern = "^\s+(\w+) (\w+) epoch (\d+): train ([\d.]+) val ([\d.]+) \((\d+)s\)"
$start = Get-Date

function Bar($frac, $width = 30) {
    $f = [double]$frac
    if ($f -lt 0) { $f = 0.0 } elseif ($f -gt 1) { $f = 1.0 }
    $n = [int][math]::Floor($f * $width)
    return "[" + ("#" * $n) + ("-" * ($width - $n)) + "] " + ("{0,5:N1}%" -f ($f * 100))
}

while ($true) {
    Clear-Host
    $done = @{}
    foreach ($ds in "liar", "isot") {
        $f = Join-Path $logs ("figs_" + $ds + ".log")
        if (Test-Path $f) {
            foreach ($m in (Select-String -Path $f -Pattern $pattern)) {
                $g = $m.Matches[0].Groups
                $key = $g[1].Value + "|" + $g[2].Value
                if (-not $done.ContainsKey($key)) { $done[$key] = @() }
                $done[$key] += [double]$g[6].Value
            }
        }
    }
    $totalSecs = 0.0; $doneSecs = 0.0; $lines = @()
    foreach ($j in $jobs) {
        $key = $j.Ds + "|" + $j.Model
        $times = @(); if ($done.ContainsKey($key)) { $times = @($done[$key]) }
        $per = $j.Guess; if ($times.Count -gt 0) { $per = ($times | Measure-Object -Average).Average }
        $totalSecs += $per * $epochs
        $doneSecs += $per * [math]::Min($times.Count, $epochs)
        $state = if ($times.Count -ge $epochs) { "done" } elseif ($times.Count -gt 0) { "running" } else { "waiting" }
        $lines += ("{0,-20} {1}  {2}/{3} epochs  ~{4:N0}s each  {5}" -f $j.Label, (Bar ($times.Count / $epochs)), $times.Count, $epochs, $per, $state)
    }
    $remain = $totalSecs - $doneSecs
    Write-Host "Training BiLSTM, BERT and BERT+BiLSTM on real data (for the figures)" -ForegroundColor Cyan
    Write-Host ("Monitor started: {0}   Now: {1}" -f $start.ToString("HH:mm:ss"), (Get-Date).ToString("HH:mm:ss"))
    Write-Host ""
    $lines | ForEach-Object { Write-Host $_ }
    Write-Host ""
    Write-Host ("OVERALL {0}" -f (Bar ($doneSecs / $totalSecs) 40)) -ForegroundColor Green
    Write-Host ("Estimated time left: {0:N0} min (finish around {1})" -f ($remain / 60), (Get-Date).AddSeconds($remain).ToString("HH:mm"))
    Write-Host "(Time left counts finished epochs only, so it is rough while an epoch is in progress.)" -ForegroundColor DarkGray
    $gpu = Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue
    if ($gpu) {
        $u = ($gpu.CounterSamples | Group-Object { ($_.InstanceName -split "_engtype_")[1] } | ForEach-Object { ($_.Group | Measure-Object CookedValue -Sum).Sum } | Measure-Object -Maximum).Maximum
        Write-Host ("GPU load (busiest engine): {0:N0}%" -f [math]::Min(100, $u))
    }
    if (Test-Path (Join-Path $logs "figs_done.log")) { Write-Host "`nALL RUNS FINISHED" -ForegroundColor Yellow; break }
    Start-Sleep -Seconds 5
}
