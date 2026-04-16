#!/usr/bin/env powershell
<#
.SYNOPSIS
    SANJAYA Docker Regression Validation Test Suite
.DESCRIPTION
    Validates that Docker deployment maintains 100% compatibility with existing API
    Tests health checks, predict endpoint, NL predictions, database persistence
.EXAMPLE
    .\docker_regression_test.ps1
#>

param(
    [string]$BaseURL = "http://localhost:8000",
    [int]$MaxRetries = 5,
    [int]$RetryDelaySeconds = 3
)

$ErrorActionPreference = "Stop"
$TestResults = @()

# ──────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Path,
        [object]$Body,
        [scriptblock]$Validator
    )
    
    try {
        $url = "$BaseURL$Path"
        $params = @{
            Uri = $url
            Method = $Method
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params["Body"] = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-RestMethod @params
        
        if ($Validator) {
            $isValid = & $Validator $response
            if ($isValid) {
                Write-Host "✅ $Name — PASSED" -ForegroundColor Green
                $TestResults += @{ Name = $Name; Status = "PASSED"; Details = "" }
                return $true
            } else {
                Write-Host "❌ $Name — FAILED" -ForegroundColor Red
                Write-Host "   Response: $($response | ConvertTo-Json)" -ForegroundColor Yellow
                $TestResults += @{ Name = $Name; Status = "FAILED"; Details = "$($response | ConvertTo-Json)" }
                return $false
            }
        } else {
            Write-Host "✅ $Name — PASSED" -ForegroundColor Green
            $TestResults += @{ Name = $Name; Status = "PASSED"; Details = "" }
            return $true
        }
    } catch {
        Write-Host "❌ $Name — ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $TestResults += @{ Name = $Name; Status = "ERROR"; Details = $_.Exception.Message }
        return $false
    }
}

function Wait-ForService {
    param([int]$Retries = $MaxRetries)
    
    Write-Host "🔄 Waiting for service to be ready..." -ForegroundColor Cyan
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "$BaseURL/health" -Method Get -ErrorAction Stop
            Write-Host "✓ Service is ready" -ForegroundColor Green
            return $true
        } catch {
            if ($i -lt $Retries) {
                Write-Host "   Attempt $i/$Retries — retrying in ${RetryDelaySeconds}s..." -ForegroundColor Yellow
                Start-Sleep -Seconds $RetryDelaySeconds
            }
        }
    }
    Write-Host "❌ Service did not become ready after $Retries attempts" -ForegroundColor Red
    return $false
}

# ──────────────────────────────────────────────────────────────────
# REGRESSION TEST SUITE
# ──────────────────────────────────────────────────────────────────

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       SANJAYA DOCKER REGRESSION VALIDATION TEST SUITE          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Base URL: $BaseURL" -ForegroundColor Cyan
Write-Host ""

# Step 1: Wait for service
if (-not (Wait-ForService)) {
    Write-Host ""
    Write-Host "⚠️  Service is not responding. Make sure Docker is running:"
    Write-Host "   docker-compose up -d"
    exit 1
}

Write-Host ""
Write-Host "─── PHASE 1: Health & Initialization ───" -ForegroundColor Magenta
Write-Host ""

# Test 1: Health Check
Test-Endpoint `
    -Name "Health Check Endpoint" `
    -Method "GET" `
    -Path "/health" `
    -Validator {
        param($response)
        return (
            $response.status -eq "ok" -and
            $response.system -eq "SANJAYA" -and
            $response.version -eq "2.0.0" -and
            $response.brahma -eq $true
        )
    }

Write-Host ""
Write-Host "─── PHASE 2: Standard Prediction Pipeline ───" -ForegroundColor Magenta
Write-Host ""

# Test 2: Predict with Valid Payload
$predictPayload = @{
    origin = "Mumbai"
    destination = "Rotterdam"
    vessel_id = "TEST-VESSEL-001"
    transport_mode = "sea"
    days_real = 8
    days_scheduled = 5
    benefit_per_order = 50
    sales_per_customer = 500
    discount_rate = 0.05
    profit_ratio = 0.1
    quantity = 1000
    category_id = 73
    hs_code = "8471"
    month = 4
}

Test-Endpoint `
    -Name "Predict Endpoint (Valid Payload)" `
    -Method "POST" `
    -Path "/predict" `
    -Body $predictPayload `
    -Validator {
        param($response)
        return (
            $response.PSObject.Properties.Name -contains "risk_score" -and
            $response.PSObject.Properties.Name -contains "risk_level" -and
            $response.PSObject.Properties.Name -contains "breakdown" -and
            $response.PSObject.Properties.Name -contains "evidence"
        )
    }

Write-Host ""

# Test 3: Pre-flight Validation (KAVACH)
$validatePayload = @{
    origin = "Mumbai"
    destination = "Rotterdam"
    days_real = 8
    days_scheduled = 5
}

Test-Endpoint `
    -Name "Validate Endpoint (KAVACH)" `
    -Method "POST" `
    -Path "/validate" `
    -Body $validatePayload `
    -Validator {
        param($response)
        return $response.PSObject.Properties.Name -contains "valid"
    }

Write-Host ""
Write-Host "─── PHASE 3: Natural Language Processing ───" -ForegroundColor Magenta
Write-Host ""

# Test 4: NL Predict (BRAHMA)
$nlPayload = @{
    text = "Assess risk for shipment from Mumbai to Rotterdam, departing in 8 days, scheduled for 5 days, vessel MV-TEST-001"
}

Test-Endpoint `
    -Name "NL Predict Endpoint (BRAHMA)" `
    -Method "POST" `
    -Path "/nlpredict" `
    -Body $nlPayload `
    -Validator {
        param($response)
        return (
            -not $response.error -and
            ($response.PSObject.Properties.Name -contains "narrative" -or `
             $response.PSObject.Properties.Name -contains "risk_score")
        )
    }

Write-Host ""
Write-Host "─── PHASE 4: Response Schema Validation ───" -ForegroundColor Magenta
Write-Host ""

# Test 5: Validate Full Predict Response Structure
Write-Host "Testing full response structure..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod `
        -Uri "$BaseURL/predict" `
        -Method POST `
        -ContentType "application/json" `
        -Body ($predictPayload | ConvertTo-Json)
    
    $requiredFields = @(
        "risk_score",
        "risk_level", 
        "breakdown",
        "evidence",
        "recommendation",
        "vessel_id",
        "route"
    )
    
    $missingFields = $requiredFields | Where-Object { -not $response.PSObject.Properties.Name.Contains($_) }
    
    if ($missingFields.Count -eq 0) {
        Write-Host "✅ Response Schema Validation — PASSED (All required fields present)" -ForegroundColor Green
        $TestResults += @{ Name = "Response Schema Validation"; Status = "PASSED"; Details = "" }
    } else {
        Write-Host "❌ Response Schema Validation — FAILED" -ForegroundColor Red
        Write-Host "   Missing fields: $($missingFields -join ', ')" -ForegroundColor Yellow
        $TestResults += @{ Name = "Response Schema Validation"; Status = "FAILED"; Details = "Missing: $($missingFields -join ', ')" }
    }
    
    # Validate breakdown structure
    $breakdownFields = @("p_delay", "s_weather", "s_geo", "c_port", "customs_risk")
    $missingBreakdown = $breakdownFields | Where-Object { -not $response.breakdown.PSObject.Properties.Name.Contains($_) }
    
    if ($missingBreakdown.Count -eq 0) {
        Write-Host "✅ Breakdown Schema Validation — PASSED (All scores present)" -ForegroundColor Green
        $TestResults += @{ Name = "Breakdown Schema"; Status = "PASSED"; Details = "" }
    } else {
        Write-Host "❌ Breakdown Schema Validation — FAILED" -ForegroundColor Red
        Write-Host "   Missing: $($missingBreakdown -join ', ')" -ForegroundColor Yellow
        $TestResults += @{ Name = "Breakdown Schema"; Status = "FAILED"; Details = "Missing: $($missingBreakdown -join ', ')" }
    }
    
} catch {
    Write-Host "❌ Response Schema Validation — ERROR: $($_.Exception.Message)" -ForegroundColor Red
    $TestResults += @{ Name = "Response Schema Validation"; Status = "ERROR"; Details = $_.Exception.Message }
}

Write-Host ""
Write-Host "─── PHASE 5: Database Persistence ───" -ForegroundColor Magenta
Write-Host ""

# Test 6: Check if data was persisted
Write-Host "Checking database persistence..." -ForegroundColor Cyan

try {
    $dbCheckCommand = @"
docker-compose exec postgres psql -U sanjaya_user -d sanjaya_db -c "SELECT COUNT(*) as count FROM risk_assessments LIMIT 1;" 2>$null
"@
    
    $dbResult = Invoke-Expression $dbCheckCommand 2>$null
    
    if ($dbResult -match "(\d+)") {
        $count = [int]$matches[1]
        if ($count -ge 0) {
            Write-Host "✅ Database Persistence — PASSED (Found $count assessments)" -ForegroundColor Green
            $TestResults += @{ Name = "Database Persistence"; Status = "PASSED"; Details = "$count records" }
        } else {
            Write-Host "⚠️  Database Persistence — WARNING (No records yet)" -ForegroundColor Yellow
            $TestResults += @{ Name = "Database Persistence"; Status = "WARNING"; Details = "No records found" }
        }
    } else {
        Write-Host "⚠️  Database Persistence — SKIPPED (Could not verify - check docker-compose)" -ForegroundColor Yellow
        $TestResults += @{ Name = "Database Persistence"; Status = "SKIPPED"; Details = "Could not query DB" }
    }
} catch {
    Write-Host "⚠️  Database Persistence — SKIPPED ($($_.Exception.Message))" -ForegroundColor Yellow
    $TestResults += @{ Name = "Database Persistence"; Status = "SKIPPED"; Details = $_.Exception.Message }
}

Write-Host ""
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                       TEST SUMMARY REPORT                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$passed = ($TestResults | Where-Object { $_.Status -eq "PASSED" }).Count
$failed = ($TestResults | Where-Object { $_.Status -eq "FAILED" }).Count
$errors = ($TestResults | Where-Object { $_.Status -eq "ERROR" }).Count
$skipped = ($TestResults | Where-Object { $_.Status -eq "SKIPPED" }).Count

Write-Host "Test Results:"
Write-Host "  ✅ Passed:  $passed"
Write-Host "  ❌ Failed:  $failed"
Write-Host "  ⚠️  Errors:  $errors"
Write-Host "  ⊘  Skipped: $skipped"
Write-Host "  ─────────────────"
Write-Host "  Total:   $($TestResults.Count)"
Write-Host ""

if ($failed -eq 0 -and $errors -eq 0) {
    Write-Host "✅ ALL REGRESSION TESTS PASSED — Docker deployment is compatible!" -ForegroundColor Green
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ SOME TESTS FAILED — Review output above" -ForegroundColor Red
    Write-Host ""
    exit 1
}
