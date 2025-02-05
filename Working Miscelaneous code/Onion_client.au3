#include <GUIConstantsEx.au3>
#include <ButtonConstants.au3>
#include <EditConstants.au3>
#include <WindowsConstants.au3>

Global $g_TCPConnected = False
Global $g_TCPSocket = -1
Global $g_ServerIP = "127.0.0.1"
Global $g_ServerPort = 12345
Global $g_BufferSize = 4096

; Create the GUI
Global $hGUI = GUICreate("TCP Client", 400, 200)
Global $btnConnect = GUICtrlCreateButton("Connect to Server", 20, 50, 150, 30)
Global $btnDisconnect = GUICtrlCreateButton("Disconnect", 200, 50, 150, 30)
Global $lblStatus = GUICtrlCreateLabel("Status: Disconnected", 20, 100, 360, 20)
Global $btnEnterChallenge = GUICtrlCreateButton("ENTER_CHALLENGE_MISSION", 100, 150, 200, 40)
Global $lblAgentID = GUICtrlCreateLabel("message: Not received", 20, 120, 300, 30)


GUISetState(@SW_SHOW)

; Initialize TCP
TCPStartup()

While 1
    Switch GUIGetMsg()
        Case $GUI_EVENT_CLOSE
            ExitLoop
        Case $btnConnect
            If Not $g_TCPConnected Then ConnectToServer()
        Case $btnDisconnect
            If $g_TCPConnected Then DisconnectFromServer()
		Case $btnEnterChallenge
            If $g_TCPConnected Then
                Local $agentID = EnterChallenge()
                GUICtrlSetData($lblAgentID, "Result: " & $agentID)
            EndIf
    EndSwitch
    
    ; If connected, check for messages from the server
    If $g_TCPConnected Then
        CheckForServerMessage()
    EndIf
    
    Sleep(100) ; Add a delay for smooth GUI operation
WEnd

; Clean up before exiting
DisconnectFromServer()
TCPShutdown()
GUIDelete($hGUI)
Exit

; Function to connect to the server
Func ConnectToServer()
    $g_TCPSocket = TCPConnect($g_ServerIP, $g_ServerPort)
    If @error Then
        GUICtrlSetData($lblStatus, "Status: Connection failed!")
        Return
    EndIf
    $g_TCPConnected = True
    GUICtrlSetData($lblStatus, "Status: Connected to " & $g_ServerIP & ":" & $g_ServerPort)
    
    ; Send an initial message to the server
    SendMessageToServer("Hello from AutoIt!")
EndFunc

; Function to disconnect from the server
Func DisconnectFromServer()
    If $g_TCPConnected And $g_TCPSocket <> -1 Then
        TCPCloseSocket($g_TCPSocket)
        $g_TCPSocket = -1
        $g_TCPConnected = False
        GUICtrlSetData($lblStatus, "Status: Disconnected")
    EndIf
EndFunc

; Function to send a message to the server
Func SendMessageToServer($message)
    If Not $g_TCPConnected Then Return
    TCPSend($g_TCPSocket, $message)
    GUICtrlSetData($lblStatus, "Status: Sent '" & $message & "'")
EndFunc

; Function to check for messages from the server
Func CheckForServerMessage()
    If Not $g_TCPConnected Then Return
    Local $received = TCPRecv($g_TCPSocket, $g_BufferSize)
    If $received = "" Then
        ; If nothing received, check for disconnection
        If @error Then
            GUICtrlSetData($lblStatus, "Status: Server disconnected!")
            DisconnectFromServer()
        EndIf
        Return
    EndIf
    
    ; Display the received message
    GUICtrlSetData($lblStatus, "Server: " & $received)
EndFunc

Func RequestAgentID()
    If Not $g_TCPConnected Then Return "Not connected"
	
	Local $timer = TimerInit() ; Start timing

    TCPSend($g_TCPSocket, "GET_AGENT_ID")
	
    Local $response = ""
    Local $maxWaitTime = 5000 
	
	While TimerDiff($timer) < $maxWaitTime
        $response = TCPRecv($g_TCPSocket, 1024)
        If $response <> "" Then ExitLoop
        Sleep(1) ; Minimize CPU usage while looping
    WEnd
    
	Local $elapsedTime = TimerDiff($timer) ; Measure time in milliseconds
    
    
    If $response = "" Then
        Return "No response (Time: " & Round($elapsedTime, 2) & " ms)"
    EndIf

    Return "Agent ID: " & StringStripWS($response, 3) & " (Time: " & Round($elapsedTime, 2) & " ms)"
EndFunc

Func EnterChallenge()
    If Not $g_TCPConnected Then Return "Not connected"
	
	Local $timer = TimerInit() ; Start timing

    TCPSend($g_TCPSocket, "ENTER_CHALLENGE_MISSION")
	
    Local $response = ""
    Local $maxWaitTime = 5000 
	
	While TimerDiff($timer) < $maxWaitTime
        $response = TCPRecv($g_TCPSocket, 1024)
        If $response <> "" Then ExitLoop
        Sleep(1) ; Minimize CPU usage while looping
    WEnd
    
	Local $elapsedTime = TimerDiff($timer) ; Measure time in milliseconds
    
    
    If $response = "" Then
        Return "No response (Time: " & Round($elapsedTime, 2) & " ms)"
    EndIf

    Return "Agent ID: " & StringStripWS($response, 3) & " (Time: " & Round($elapsedTime, 2) & " ms)"
EndFunc