# SSH to dory through the existing ADB USB connection; no new Windows driver.
param(
    [string]$Adb = "adb",
    [int]$LocalPort = 2222,
    [string]$User = "root"
)

$ErrorActionPreference = "Stop"

& $Adb get-state | Out-Null
if ($LASTEXITCODE -ne 0) { throw "ADB device is not ready." }

& $Adb forward "tcp:$LocalPort" "tcp:22" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "ADB port forward failed." }

try {
    & ssh -o "HostKeyAlias=lg-dory-adb" -p $LocalPort "${User}@127.0.0.1"
    exit $LASTEXITCODE
}
finally {
    & $Adb forward --remove "tcp:$LocalPort" | Out-Null
}
