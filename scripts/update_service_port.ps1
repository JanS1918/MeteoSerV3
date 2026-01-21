param(
	[int]$Port = 8080,
	[string]$Host = '0.0.0.0'
)

$ErrorActionPreference = 'Stop'

$svcName = 'MeteoSerBackend'
$nssm = 'C:\Users\kioko\Desktop\MeteoSerV3\tools\nssm\nssm-2.24\win64\nssm.exe'

# Obtener entorno actual y actualizar METEOSER_HOST/METEOSER_PORT sin perder el resto
$current = & $nssm get $svcName AppEnvironmentExtra 2>$null
$lines = @()
if ($LASTEXITCODE -eq 0 -and $current) {
	$lines = $current -split "`r?`n" | Where-Object { $_ -and $_.Trim() -ne '' }
}

$lines = $lines | Where-Object { $_ -notmatch '^METEOSER_HOST=' -and $_ -notmatch '^METEOSER_PORT=' }
$lines += "METEOSER_HOST=$Host"
$lines += "METEOSER_PORT=$Port"

& $nssm set $svcName AppEnvironmentExtra ($lines -join "`r`n")
& $nssm restart $svcName
