<#
.SYNOPSIS
    Secure local interactive helper to configure backend/.env for NEXORA AI.
.DESCRIPTION
    Prompts for the nexora_app password securely with masked input (characters not displayed).
    URL-encodes any special characters in the password.
    Writes backend/.env with DATABASE_URL and TEST_DATABASE_URL without printing secrets to logs or console.
#>

$envPath = "E:\NEXORA_AI\backend\.env"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  NEXORA AI - Secure PostgreSQL Local Credential Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target Role:      nexora_app"
Write-Host "Dev Database:     nexora_dev"
Write-Host "Test Database:    nexora_test"
Write-Host "Host & Port:      127.0.0.1:5432"
Write-Host ""
Write-Host "Enter the password you assigned to role 'nexora_app'." -ForegroundColor Yellow
Write-Host "(Your typing will be completely masked - characters will NOT appear on screen):" -ForegroundColor Gray

$securePassword = Read-Host -AsSecureString "nexora_app Password"

if ($null -eq $securePassword -or $securePassword.Length -eq 0) {
    Write-Host "Error: Password cannot be empty." -ForegroundColor Red
    exit 1
}

# Convert SecureString to plain text in memory strictly for URL encoding
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

# RFC 3986 URL Encoding of special characters
$encodedPassword = [System.Uri]::EscapeDataString($plainPassword)
$plainPassword = $null

$devUrl = "postgresql+asyncpg://nexora_app:$encodedPassword@127.0.0.1:5432/nexora_dev"
$testUrl = "postgresql+asyncpg://nexora_app:$encodedPassword@127.0.0.1:5432/nexora_test"
$encodedPassword = $null

$envContent = @"
# ==============================================================================
# NEXORA AI - Local Development Environment Configuration
# ==============================================================================
APP_ENV=development
APP_NAME=NEXORA AI
APP_DEBUG=true
API_V1_STR=/api/v1
SECRET_KEY=nexora-local-dev-secret-key-32bytes-secure-minimum-hash

SERVER_HOST=127.0.0.1
SERVER_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

ARGON2_TIME_COST=2
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4
ARGON2_HASH_LEN=32
ARGON2_SALT_LEN=16

# Primary Development Database (Used by backend app and Alembic migrations)
DATABASE_URL=$devUrl

# Isolated Test Database (Used exclusively by integration test suite)
TEST_DATABASE_URL=$testUrl

AI_PROVIDER=local
GEMINI_API_KEY=
AI_TIMEOUT_SECONDS=10

SANDBOX_MODE=disabled
SANDBOX_TIMEOUT_SECONDS=5
SANDBOX_MEMORY_LIMIT_MB=128
SANDBOX_MAX_OUTPUT_BYTES=65536
"@

# Write to backend/.env
Set-Content -Path $envPath -Value $envContent -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "SUCCESS: backend/.env has been created securely." -ForegroundColor Green
Write-Host "File path: $envPath" -ForegroundColor Gray
Write-Host "Zero secrets were printed to console or logs." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
