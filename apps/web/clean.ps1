# Clean Next.js cache and rebuild
Write-Host "Cleaning Next.js cache..." -ForegroundColor Yellow

if (Test-Path ".next") {
    Remove-Item -Recurse -Force ".next"
    Write-Host "Removed .next directory" -ForegroundColor Green
}

if (Test-Path "node_modules/.cache") {
    Remove-Item -Recurse -Force "node_modules/.cache"
    Write-Host "Removed node_modules/.cache" -ForegroundColor Green
}

Write-Host "Cache cleaned successfully!" -ForegroundColor Green
Write-Host "Run 'npm run dev' to start the development server" -ForegroundColor Cyan
