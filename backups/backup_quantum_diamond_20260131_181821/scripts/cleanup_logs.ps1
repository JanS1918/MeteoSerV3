Remove-Item 'C:\mosquitto\log\mosquitto.log' -ErrorAction SilentlyContinue -Force
Remove-Item 'C:\mosquitto\log\mosquitto_stdout.log' -ErrorAction SilentlyContinue -Force
Remove-Item 'C:\mosquitto\log\mosquitto_stderr.log' -ErrorAction SilentlyContinue -Force
& 'C:\Windows\System32\icacls.exe' 'C:\mosquitto\log'
