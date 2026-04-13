$lines = Get-Content 'D:\SANJAYA\sanjaya\dashboard.html' -TotalCount 1618
Set-Content -Path 'D:\SANJAYA\sanjaya\dashboard.html' -Value $lines -Encoding UTF8
Write-Host "Truncated to 1618 lines"
