#include <GUIConstantsEx.au3>
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
