
On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")
Dim result
result = WshShell.Run(""""C:\pythontotal\python1\pythonw.exe"""" & " " & """"C:\cursor\test\my_app_platform\programs\snake.py"""", 1, False)
If Err.Number <> 0 Then
    WScript.Echo "Error: " & Err.Description
End If
