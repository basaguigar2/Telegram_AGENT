# Registra el bot de Telegram de JARVIS para que arranque solo al iniciar
# sesión en Windows y siga corriendo indefinidamente en segundo plano.
#
# Ejecutar UNA VEZ desde PowerShell (clic derecho -> "Ejecutar con PowerShell",
# o pegar el contenido en una ventana de PowerShell). Si aparece un aviso de
# permisos (UAC), acepta.

# Ruta fija (no depende de $PSScriptRoot, que puede quedar vacío si el
# script se pega directamente en la consola en vez de ejecutarse como archivo).
$rutaLanzador = "C:\Users\basag\OneDrive\Documentos\JARVIS\04_Implementation\telegram_bot\run_bot.bat"

if (-not (Test-Path $rutaLanzador)) {
    Write-Host "ERROR: no encuentro $rutaLanzador -- revisa que la ruta sea correcta." -ForegroundColor Red
    exit 1
}

$accion = New-ScheduledTaskAction -Execute $rutaLanzador
$disparador = New-ScheduledTaskTrigger -AtLogOn

$config = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -Hidden

try {
    Register-ScheduledTask `
        -TaskName "JARVIS Telegram Bot" `
        -Action $accion `
        -Trigger $disparador `
        -Settings $config `
        -Description "Bot de Telegram de JARVIS -- corre en segundo plano mientras la sesion este iniciada" `
        -Force `
        -ErrorAction Stop | Out-Null
}
catch {
    Write-Host ""
    Write-Host "ERROR: no se pudo registrar la tarea." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Causa mas probable: PowerShell no se abrio como Administrador."
    Write-Host "Cierra esta ventana, busca PowerShell, clic derecho -> 'Ejecutar como administrador',"
    Write-Host "vuelve a la carpeta con cd y ejecuta este script otra vez."
    exit 1
}

Write-Host ""
Write-Host "Tarea 'JARVIS Telegram Bot' registrada correctamente." -ForegroundColor Green
Write-Host "Se iniciara automaticamente la proxima vez que inicies sesion en Windows."
Write-Host ""
Write-Host "Para arrancarla ahora mismo sin reiniciar, ejecuta:"
Write-Host "    Start-ScheduledTask -TaskName 'JARVIS Telegram Bot'"
Write-Host ""
Write-Host "Para pararla:"
Write-Host "    Stop-ScheduledTask -TaskName 'JARVIS Telegram Bot'"
Write-Host ""
Write-Host "Para quitarla del todo:"
Write-Host "    Unregister-ScheduledTask -TaskName 'JARVIS Telegram Bot' -Confirm:`$false"
