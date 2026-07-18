#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         Dharma Blurton

 Script Function:
	Forcibly terminate all GW client window handles. This will clean any running but hidden clients that have not fully closed.

#ce ----------------------------------------------------------------------------

; Script Start
#RequireAdmin

Local $aProcessList = ProcessList("Gw.exe")

For $i = 1 To $aProcessList[0][0]
    ProcessClose($aProcessList[$i][1])
Next