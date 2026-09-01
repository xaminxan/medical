Set WshShell = CreateObject("WScript.Shell")
' 请把下面的路径换成你刚才创建的 bat 文件的绝对路径
WshShell.Run chr(34) & "D:\Python\Pythonevn\start_server.bat" & Chr(34), 0
Set WshShell = Nothing