@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo SAT Solver API - Complete curl Test Suite
echo ============================================================
echo.

set BASE_URL=http://127.0.0.1:8008
set PASS=0
set FAIL=0

echo [1/10] Testing root endpoint...
curl.exe -s -X GET "%BASE_URL%/" -o "test_01_root.json"
if %errorlevel%==0 (
    echo   PASS: Root endpoint responded
    set /A PASS+=1
) else (
    echo   FAIL: Root endpoint error
    set /A FAIL+=1
)
echo.

echo [2/10] Testing DIMACS parse...
curl.exe -s -X POST "%BASE_URL%/api/dimacs/parse" -H "Content-Type: application/json" --data-binary "@test_parse_request.json" -o "test_02_parse.json"
if %errorlevel%==0 (
    echo   PASS: DIMACS parsed successfully
    set /A PASS+=1
) else (
    echo   FAIL: DIMACS parse error
    set /A FAIL+=1
)
echo.

echo [3/10] Testing DPLL SAT solve...
curl.exe -s -X POST "%BASE_URL%/api/solve/dpll" -H "Content-Type: application/json" --data-binary "@test_parse_request.json" -o "test_03_dpll_sat.json"
if %errorlevel%==0 (
    echo   PASS: DPLL SAT solve completed
    set /A PASS+=1
) else (
    echo   FAIL: DPLL SAT solve error
    set /A FAIL+=1
)
echo.

echo [4/10] Testing CDCL SAT solve...
curl.exe -s -X POST "%BASE_URL%/api/solve/cdcl" -H "Content-Type: application/json" --data-binary "@test_parse_request.json" -o "test_04_cdcl_sat.json"
if %errorlevel%==0 (
    echo   PASS: CDCL SAT solve completed
    set /A PASS+=1
) else (
    echo   FAIL: CDCL SAT solve error
    set /A FAIL+=1
)
echo.

echo [5/10] Testing CDCL UNSAT solve...
curl.exe -s -X POST "%BASE_URL%/api/solve/cdcl" -H "Content-Type: application/json" --data-binary "@test_cdcl_unsat_request.json" -o "test_05_cdcl_unsat.json"
if %errorlevel%==0 (
    echo   PASS: CDCL UNSAT solve completed
    set /A PASS+=1
) else (
    echo   FAIL: CDCL UNSAT solve error
    set /A FAIL+=1
)
echo.

echo [6/10] Testing random 3-SAT generation...
curl.exe -s -X POST "%BASE_URL%/api/generate/random" -H "Content-Type: application/json" --data-binary "@test_gen_random_request.json" -o "test_06_gen_random.json"
if %errorlevel%==0 (
    echo   PASS: Random 3-SAT generated successfully
    set /A PASS+=1
) else (
    echo   FAIL: Random generation error
    set /A FAIL+=1
)
echo.

echo [7/10] Testing pigeonhole formula generation...
curl.exe -s -X POST "%BASE_URL%/api/generate/pigeonhole" -H "Content-Type: application/json" --data-binary "@test_gen_pigeonhole_request.json" -o "test_07_gen_pigeonhole.json"
if %errorlevel%==0 (
    echo   PASS: Pigeonhole formula generated successfully
    set /A PASS+=1
) else (
    echo   FAIL: Pigeonhole generation error
    set /A FAIL+=1
)
echo.

echo [8/10] Testing Sudoku solve...
curl.exe -s -X POST "%BASE_URL%/api/sudoku/solve" -H "Content-Type: application/json" --data-binary "@test_sudoku_request.json" -o "test_08_sudoku_solve.json"
if %errorlevel%==0 (
    echo   PASS: Sudoku solve completed
    set /A PASS+=1
) else (
    echo   FAIL: Sudoku solve error
    set /A FAIL+=1
)
echo.

echo [9/10] Getting Sudoku puzzles...
curl.exe -s -X GET "%BASE_URL%/api/sudoku/puzzles" -o "test_09_sudoku_puzzles.json"
if %errorlevel%==0 (
    echo   PASS: Sudoku puzzles retrieved
    set /A PASS+=1
) else (
    echo   FAIL: Sudoku puzzles error
    set /A FAIL+=1
)
echo.

echo [10/10] Getting benchmark cases...
curl.exe -s -X GET "%BASE_URL%/api/benchmarks/cases" -o "test_10_benchmark_cases.json"
if %errorlevel%==0 (
    echo   PASS: Benchmark cases retrieved
    set /A PASS+=1
) else (
    echo   FAIL: Benchmark cases error
    set /A FAIL+=1
)
echo.

echo ============================================================
echo Test Summary: %PASS% passed, %FAIL% failed
echo ============================================================
echo.

echo [Verification] Checking SAT assignment validity...
findstr /C:"\"assignment_valid\": true" "test_04_cdcl_sat.json" >nul
if %errorlevel%==0 (
    echo   PASS: SAT assignment is valid
) else (
    echo   FAIL: SAT assignment invalid or missing
)

echo [Verification] Checking UNSAT result...
findstr /C:"\"sat\": false" "test_05_cdcl_unsat.json" >nul
if %errorlevel%==0 (
    echo   PASS: UNSAT result correct
) else (
    echo   FAIL: UNSAT result incorrect
)

echo [Verification] Checking proof output...
findstr /C:"\"proof\":" "test_05_cdcl_unsat.json" >nul
if %errorlevel%==0 (
    echo   PASS: Proof output present
) else (
    echo   FAIL: Proof output missing
)

echo [Verification] Checking Sudoku solution...
findstr /C:"\"sat\": true" "test_08_sudoku_solve.json" >nul
if %errorlevel%==0 (
    echo   PASS: Sudoku solution found
) else (
    echo   FAIL: Sudoku solution missing
)

echo [Verification] Checking benchmark cases count...
findstr /C:"\"name\":" "test_10_benchmark_cases.json" | find /C "\"name\":" > temp_count.txt
set /p COUNT=<temp_count.txt
del temp_count.txt
if %COUNT% GEQ 5 (
    echo   PASS: At least 5 benchmark cases available
) else (
    echo   FAIL: Less than 5 benchmark cases
)

echo.
echo ============================================================
echo All tests completed!
echo ============================================================
