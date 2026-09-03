Write-Host "Creating offline package directories..."
New-Item -ItemType Directory -Force -Path "offline_packages\python" | Out-Null
New-Item -ItemType Directory -Force -Path "offline_packages\npm" | Out-Null

Write-Host "Downloading Python dependencies..."
python -m pip download -r backend\requirements.txt -d offline_packages\python

Write-Host "Populating npm cache..."
Set-Location frontend
npm install --cache ..\offline_packages\npm
Set-Location ..

Write-Host "Offline packages have been downloaded successfully."
