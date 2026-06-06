$ErrorActionPreference = "Stop"

Write-Host "Testing CDCL UNSAT formula..."

$body = @{
    dimacs = "p cnf 2 4`n1 2 0`n1 -2 0`n-1 2 0`n-1 -2 0"
    enable_proof = $true
}

$json = $body | ConvertTo-Json
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)

try {
    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8008/api/solve/cdcl" -Method POST -Body $bytes -ContentType "application/json" -UseBasicParsing -TimeoutSec 30
    $data = $resp.Content | ConvertFrom-Json
    
    $result = @()
    $result += "CDCL UNSAT test:"
    $result += "  SAT: $($data.sat)"
    $result += "  Time: $($data.time_seconds)s"
    $result += "  Conflicts: $($data.conflicts)"
    $result += "  Restarts: $($data.restarts)"
    $result += "  Learnt clauses: $($data.learnt_clauses)"
    if ($data.proof) {
        $result += "  Proof length: $($data.proof.Length)"
        if ($data.proof.Length -gt 0) {
            $result += "  First 3 proof steps:"
            for ($i = 0; $i -lt [Math]::Min(3, $data.proof.Length); $i++) {
                $result += "    $($i+1): $($data.proof[$i] -join ' ')"
            }
        }
    }
    
    $result | ForEach-Object { Write-Host $_ }
    
    $result | Out-File -FilePath "cdcl_unsat_test_result.txt" -Encoding utf8
}
catch {
    Write-Host "Error: $_"
    $_.Exception.Message | Out-File -FilePath "cdcl_unsat_test_result.txt" -Encoding utf8
}
