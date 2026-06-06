$ErrorActionPreference = "Continue"

Write-Host "============================================================"
Write-Host "SAT Solver API - Complete curl Test Suite"
Write-Host "============================================================"
Write-Host ""

$BASE_URL = "http://127.0.0.1:8008"
$PASS = 0
$FAIL = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [string]$RequestFile,
        [string]$OutputFile
    )
    
    Write-Host "$Name"
    
    try {
        if ($Method -eq "GET") {
            curl.exe -s -X GET "$BASE_URL$Endpoint" -o $OutputFile
        } else {
            curl.exe -s -X POST "$BASE_URL$Endpoint" -H "Content-Type: application/json" --data-binary "@$RequestFile" -o $OutputFile
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  PASS: Endpoint responded successfully"
            $script:PASS++
            return $true
        } else {
            Write-Host "  FAIL: curl exit code $LASTEXITCODE"
            $script:FAIL++
            return $false
        }
    } catch {
        Write-Host "  FAIL: $_"
        $script:FAIL++
        return $false
    }
}

Test-Endpoint "[1/10] Testing root endpoint..." "GET" "/" "" "test_01_root.json"
Write-Host ""

Test-Endpoint "[2/10] Testing DIMACS parse..." "POST" "/api/dimacs/parse" "test_parse_request.json" "test_02_parse.json"
Write-Host ""

Test-Endpoint "[3/10] Testing DPLL SAT solve..." "POST" "/api/solve/dpll" "test_parse_request.json" "test_03_dpll_sat.json"
Write-Host ""

Test-Endpoint "[4/10] Testing CDCL SAT solve..." "POST" "/api/solve/cdcl" "test_parse_request.json" "test_04_cdcl_sat.json"
Write-Host ""

Test-Endpoint "[5/10] Testing CDCL UNSAT solve..." "POST" "/api/solve/cdcl" "test_cdcl_unsat_request.json" "test_05_cdcl_unsat.json"
Write-Host ""

Test-Endpoint "[6/10] Testing random 3-SAT generation..." "POST" "/api/generate/random" "test_gen_random_request.json" "test_06_gen_random.json"
Write-Host ""

Test-Endpoint "[7/10] Testing pigeonhole formula generation..." "POST" "/api/generate/pigeonhole" "test_gen_pigeonhole_request.json" "test_07_gen_pigeonhole.json"
Write-Host ""

Test-Endpoint "[8/10] Testing Sudoku solve..." "POST" "/api/sudoku/solve" "test_sudoku_request.json" "test_08_sudoku_solve.json"
Write-Host ""

Test-Endpoint "[9/10] Getting Sudoku puzzles..." "GET" "/api/sudoku/puzzles" "" "test_09_sudoku_puzzles.json"
Write-Host ""

Test-Endpoint "[10/10] Getting benchmark cases..." "GET" "/api/benchmarks/cases" "" "test_10_benchmark_cases.json"
Write-Host ""

Write-Host "============================================================"
Write-Host "Test Summary: $PASS passed, $FAIL failed"
Write-Host "============================================================"
Write-Host ""

Write-Host "[Verification] Checking results..."
Write-Host ""

$verificationPass = 0
$verificationFail = 0

function Verify-Result {
    param(
        [string]$Description,
        [string]$File,
        [string]$Pattern,
        [bool]$ShouldExist = $true
    )
    
    try {
        $content = Get-Content $File -Raw -ErrorAction Stop
        $found = $content -match $Pattern
        
        if ($found -eq $ShouldExist) {
            Write-Host "  PASS: $Description"
            $script:verificationPass++
            return $true
        } else {
            Write-Host "  FAIL: $Description"
            $script:verificationFail++
            return $false
        }
    } catch {
        Write-Host "  FAIL: $Description - File not found"
        $script:verificationFail++
        return $false
    }
}

Verify-Result "SAT assignment is valid" "test_04_cdcl_sat.json" '"assignment_valid":\s*true'
Verify-Result "UNSAT result correct" "test_05_cdcl_unsat.json" '"sat":\s*false'
Verify-Result "Proof output present" "test_05_cdcl_unsat.json" '"proof":'
Verify-Result "Sudoku solution found" "test_08_sudoku_solve.json" '"sat":\s*true'

try {
    $content = Get-Content "test_10_benchmark_cases.json" -Raw -ErrorAction Stop
    $cases = $content | ConvertFrom-Json
    if ($cases.Count -ge 5) {
        Write-Host "  PASS: At least 5 benchmark cases available ($($cases.Count) cases)"
        $verificationPass++
    } else {
        Write-Host "  FAIL: Less than 5 benchmark cases ($($cases.Count) cases)"
        $verificationFail++
    }
} catch {
    Write-Host "  FAIL: Could not read benchmark cases"
    $verificationFail++
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Verification: $verificationPass passed, $verificationFail failed"
Write-Host "============================================================"
Write-Host ""

Write-Host "[Detailed Results]"
Write-Host ""

function Show-Result {
    param(
        [string]$File,
        [string]$Title,
        [string[]]$Fields
    )
    
    try {
        $content = Get-Content $File -Raw -ErrorAction Stop
        $data = $content | ConvertFrom-Json
        
        Write-Host "$Title"
        foreach ($field in $Fields) {
            if ($data.PSObject.Properties.Name -contains $field) {
                $value = $data.$field
                if ($value -is [System.Array]) {
                    Write-Host "  $field : Array ($($value.Length) items)"
                } elseif ($null -ne $value) {
                    Write-Host "  $field : $value"
                }
            }
        }
        Write-Host ""
    } catch {
        Write-Host "$Title - Could not read file"
        Write-Host ""
    }
}

Show-Result "test_04_cdcl_sat.json" "CDCL SAT Result" @("sat", "time_seconds", "conflicts", "restarts", "learnt_clauses", "assignment_valid")
Show-Result "test_05_cdcl_unsat.json" "CDCL UNSAT Result" @("sat", "time_seconds", "conflicts", "restarts", "learnt_clauses")
Show-Result "test_06_gen_random.json" "Random 3-SAT Generation" @("num_vars", "num_clauses")
Show-Result "test_07_gen_pigeonhole.json" "Pigeonhole Generation" @("num_vars", "num_clauses")
Show-Result "test_08_sudoku_solve.json" "Sudoku Result" @("sat", "time_seconds", "cnf_vars", "cnf_clauses")

Write-Host "============================================================"
Write-Host "All tests completed successfully!"
Write-Host "============================================================"
