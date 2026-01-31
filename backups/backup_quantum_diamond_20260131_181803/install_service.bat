@echo off
sc.exe create MeteoSerBackend binPath=  C:\Windows\System32\cmd.exe /c C:\Users\kioko\Desktop\MeteoSerV3\start_service.bat start= auto
sc.exe description MeteoSerBackend MeteoSer backend 
sc.exe failure MeteoSerBackend reset= 30 actions= restart/60000
net start MeteoSerBackend
