$baseUrl = "http://localhost:8008"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MaxSAT API Curl Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-CurlPost($url, $body) {
    $jsonBody = $body | ConvertTo-Json -Depth 10
    $response = Invoke-WebRequest -Uri $url -Method Post -Body $jsonBody -ContentType "application/json" -UseBasicParsing
    return $response.Content | ConvertFrom-Json
}

function Invoke-CurlGet($url) {
    $response = Invoke-WebRequest -Uri $url -Method Get -UseBasicParsing
    return $response.Content | ConvertFrom-Json
}

Write-Host "Test 1: WCNF Parse" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$wcnfText = @"
c test wcnf
p wcnf 3 4 100
100 1 2 0
100 -2 3 0
5 1 0
10 -3 0
"@
$result1 = Invoke-CurlPost "$baseUrl/api/wcnf/parse" @{ wcnf = $wcnfText }
$result1 | Format-List
Write-Host ""

Write-Host "Test 2: MaxSAT Solve - Small Instance" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$wcnfSmall = Get-Content "test_instances/mixed_hard_soft_10var.wcnf" -Raw
$result2 = Invoke-CurlPost "$baseUrl/api/maxsat/solve" @{ wcnf = $wcnfSmall; max_time = 30.0 }
$result2 | Format-List
Write-Host ""

Write-Host "Test 3: MaxSAT Solve - Pure Soft" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$wcnfSoft = Get-Content "test_instances/pure_soft_8var.wcnf" -Raw
$result3 = Invoke-CurlPost "$baseUrl/api/maxsat/solve" @{ wcnf = $wcnfSoft; max_time = 30.0 }
$result3 | Format-List
Write-Host ""

Write-Host "Test 4: MaxSAT Solve - Vertex Cover" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$wcnfVC = Get-Content "test_instances/vertex_cover_6node.wcnf" -Raw
$result4 = Invoke-CurlPost "$baseUrl/api/maxsat/solve" @{ wcnf = $wcnfVC; max_time = 30.0 }
$result4 | Format-List
Write-Host ""

Write-Host "Test 5: MaxSAT Solve - 50 Variables Performance" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$wcnf50 = Get-Content "test_instances/mixed_hard_soft_50var.wcnf" -Raw
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$result5 = Invoke-CurlPost "$baseUrl/api/maxsat/solve" @{ wcnf = $wcnf50; max_time = 30.0 }
$stopwatch.Stop()
$result5 | Format-List
Write-Host "Total time including HTTP: $($stopwatch.Elapsed.TotalSeconds.ToString('F4'))s" -ForegroundColor Yellow
if ($result5.time_seconds -lt 5.0) {
    Write-Host "PASS: 50-variable instance solved in $($result5.time_seconds.ToString('F4'))s < 5s" -ForegroundColor Green
} else {
    Write-Host "FAIL: 50-variable instance took $($result5.time_seconds.ToString('F4'))s > 5s" -ForegroundColor Red
}
Write-Host ""

Write-Host "Test 6: Vertex Cover Solve End-to-End" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$body6 = @{
    num_vertices = 6
    edges = @(@(1,2), @(1,3), @(2,3), @(2,4), @(3,5), @(4,5), @(4,6), @(5,6))
    vertex_weights = @{ "1" = 10; "2" = 20; "3" = 30; "4" = 15; "5" = 25; "6" = 35 }
    max_time = 30.0
}
$result6 = Invoke-CurlPost "$baseUrl/api/vertexcover/solve" $body6
$result6 | Format-List
Write-Host ""

Write-Host "Test 7: MaxSAT Verify (Brute Force Comparison)" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$result7 = Invoke-CurlPost "$baseUrl/api/maxsat/verify" @{ wcnf = $wcnfSmall }
$result7 | Format-List
if ($result7.match) {
    Write-Host "PASS: OLL matches brute force" -ForegroundColor Green
} else {
    Write-Host "FAIL: OLL does not match brute force" -ForegroundColor Red
}
Write-Host ""

Write-Host "Test 8: MaxSAT from weighted clauses" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$body8 = @{
    weighted_clauses = @(
        @(100, @(1, 2)),
        @(100, @(-1, -2)),
        @(10, @(1)),
        @(20, @(2))
    )
    num_vars = 2
    top = 100
    max_time = 10.0
}
$result8 = Invoke-CurlPost "$baseUrl/api/maxsat/solve" $body8
$result8 | Format-List
Write-Host ""

Write-Host "Test 9: Get Test Instances" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
$result9 = Invoke-CurlGet "$baseUrl/api/maxsat/test-instances"
$instanceNames = $result9 | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
Write-Host "Available test instances: $($instanceNames -join ', ')"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
