# Dejar de trackear .pem y keys (mantenerlos en disco, no en el repo)
# Ejecutar desde la raíz del repo: .\.github\scripts\untrack-pem.ps1

Write-Host "1. Quitando .pem y keys/ del indice de Git (los archivos siguen en disco)..." -ForegroundColor Cyan
$null = git rm -r --cached license-authority/keys/ 2>$null
$null = git rm --cached license-server/public.pem 2>$null
git ls-files "*.pem" | ForEach-Object { git rm --cached $_ 2>$null }
Write-Host "2. Estado:" -ForegroundColor Cyan
git status --short
Write-Host "`nSiguiente: git add . && git commit -m 'chore: stop tracking .pem and keys' && git push origin main" -ForegroundColor Yellow
