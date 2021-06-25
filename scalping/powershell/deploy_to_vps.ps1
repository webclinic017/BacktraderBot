$filename=$args[0]
$vps_ip_address=$args[1]

$Session = New-PSSession -HostName $vps_ip_address -SSHTransport -KeyFilePath /Users/alex/.ssh/mt_vps1_id_rsa -verbose

Copy-Item -verbose -Force "/Users/alex/Cloud@Mail.Ru/_TEMP/scalping/out/strategies/$filename" -Destination "c:\MoonTrader\data\mt-core\algorithms.TO_DEPLOY" -ToSession $Session

try {
    Invoke-Command -verbose -Session $Session -FilePath ./powershell/deploy_run_on_vps.ps1 -ErrorAction Stop
} catch [Exception] {
    echo "Error while running the remote command", $_.Exception.GetType().FullName, $_.Exception.Message
    Remove-PSSession $Session
    exit 1
}

Exit-PSSession
