Stop-Process -Name "MTCore"

Start-Sleep -verbose -s 3

Move-Item -verbose -Path c:\MoonTrader\data\mt-core\algorithms.config -Destination "c:\MoonTrader\data\mt-core\algorithms.config_BACKUP" -Force

Move-Item -verbose -Path c:\MoonTrader\data\mt-core\algorithms.TO_DEPLOY -Destination "c:\MoonTrader\data\mt-core\algorithms.config" -Force

# Start-Process -verbose -FilePath c:\MoonTrader\MTCore.exe