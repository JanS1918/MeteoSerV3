$ErrorActionPreference = 'Stop'
$svcName = 'MeteoSerBackend'
$nssm = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'
& $nssm set $svcName AppParameters '-m uvicorn main_asgi:app --host 127.0.0.1 --port 8080'
& $nssm restart $svcName
