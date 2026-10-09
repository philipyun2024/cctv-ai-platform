Write-Host "Health:"
Invoke-RestMethod http://localhost:8000/health
Write-Host "Cameras:"
Invoke-RestMethod http://localhost:8000/api/v1/cameras
Write-Host "Alarms:"
Invoke-RestMethod http://localhost:8000/api/v1/alarms
