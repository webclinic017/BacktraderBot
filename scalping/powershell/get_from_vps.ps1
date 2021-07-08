$vps_ip_address=$args[0]
$remote_filename=$args[1]

$Session = New-PSSession -HostName $vps_ip_address -SSHTransport -KeyFilePath /Users/alex/.ssh/mt_vps1_id_rsa -verbose

Copy-Item -verbose -Force -FromSession $Session "c:\MoonTrader\data\mt-core\algorithms.config" -Destination $remote_filename

Exit-PSSession