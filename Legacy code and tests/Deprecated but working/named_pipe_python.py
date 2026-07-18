from Py4GWCoreLib import *

# Define paths
site_packages_path = r"C:\Users\Apo\AppData\Local\Programs\Python\Python313-32\Lib\site-packages"
pywin32_system32 = os.path.join(site_packages_path, "pywin32_system32")

# Ensure site-packages is in sys.path
if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)

# Ensure pywin32_system32 is in sys.path
if pywin32_system32 not in sys.path:
    sys.path.append(pywin32_system32)

# Load required DLLs manually (forces embedded Python to recognize them)
ctypes.windll.LoadLibrary(os.path.join(pywin32_system32, "pywintypes313.dll"))
ctypes.windll.LoadLibrary(os.path.join(pywin32_system32, "pythoncom313.dll"))

# Now try importing the modules
import pywintypes
import win32pipe
import win32file


module_name = "Pipe Handler"
server = None


class NamedPipeServer:
    def __init__(self, pipe_name, buffer_size=4096):
        self.pipe_name = f'\\\\.\\pipe\\{pipe_name}'
        self.buffer_size = buffer_size
        self.pipe_handle = None
        self.client_connected = False
        self.retry_timer = Timer()
        self.retry_timer.Start()

    def create_pipe(self):
        """Create the named pipe but do not wait for a client yet."""
        try:
            self.pipe_handle = win32pipe.CreateNamedPipe(
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                1,  # Maximum instances
                self.buffer_size,
                self.buffer_size,
                0,  # Default timeout
                None
            )
            Py4GW.Console.Log(module_name, f"Named pipe server created on {self.pipe_name}", Py4GW.Console.MessageType.Info)
        except pywintypes.error as e:
            Py4GW.Console.Log(module_name, f"Error creating named pipe: {e}", Py4GW.Console.MessageType.Error)
            self.cleanup()

    def wait_for_client(self):
        """Attempt to connect to a client using retry logic based on a timer."""
        if self.pipe_handle and not self.client_connected:
            # Check the timer to control retries
            if self.retry_timer.HasElapsed(100):  # Retry every 100ms
                try:
                    # Attempt to connect
                    win32pipe.ConnectNamedPipe(self.pipe_handle, None)
                    self.client_connected = True
                    Py4GW.Console.Log(module_name, "Client connected successfully.", Py4GW.Console.MessageType.Success)
                except pywintypes.error as e:
                    # Handle expected error codes
                    if e.winerror == 535:  # ERROR_PIPE_CONNECTED: Client already connected
                        self.client_connected = True
                        Py4GW.Console.Log(module_name, "Client already connected.", Py4GW.Console.MessageType.Info)
                    elif e.winerror == 231:  # ERROR_PIPE_LISTENING: Pipe is listening, no client connected yet
                        Py4GW.Console.Log(module_name, "Pipe server is still listening.", Py4GW.Console.MessageType.Info)
                    else:
                        Py4GW.Console.Log(module_name, f"Error during client connection attempt: {e}", Py4GW.Console.MessageType.Warning)
                finally:
                    # Reset the retry timer regardless of the outcome
                    self.retry_timer.Reset()

    def send_message(self, message):
        """Send a message to the client."""
        if self.pipe_handle and self.client_connected:
            try:
                win32file.WriteFile(self.pipe_handle, message.encode())
                Py4GW.Console.Log(module_name, f"Sent: {message}", Py4GW.Console.MessageType.Info)
            except pywintypes.error as e:
                Py4GW.Console.Log(module_name, f"Error sending message: {e}", Py4GW.Console.MessageType.Error)
                self.handle_disconnect()

    def receive_message(self):
        """Receive a message from the client."""
        if self.pipe_handle and self.client_connected:
            try:
                result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
                message = data.decode()
                Py4GW.Console.Log(module_name, f"Received: {message}", Py4GW.Console.MessageType.Info)
                return message
            except pywintypes.error as e:
                Py4GW.Console.Log(module_name, f"Error receiving message: {e}", Py4GW.Console.MessageType.Error)
                self.handle_disconnect()
                return None

    def handle_disconnect(self):
        """Handle client disconnection and prepare for a new connection."""
        if self.pipe_handle and self.client_connected:
            try:
                win32pipe.DisconnectNamedPipe(self.pipe_handle)
                Py4GW.Console.Log(module_name, "Client disconnected. Pipe instance released.", Py4GW.Console.MessageType.Info)
            except pywintypes.error as e:
                Py4GW.Console.Log(module_name, f"Error during disconnection: {e}", Py4GW.Console.MessageType.Warning)
            finally:
                self.client_connected = False

    def cleanup(self):
        """Clean up the named pipe."""
        if self.pipe_handle:
            try:
                # Disconnect the pipe if it is connected
                if self.client_connected:
                    win32pipe.DisconnectNamedPipe(self.pipe_handle)
                    Py4GW.Console.Log(module_name, "Pipe instance disconnected.", Py4GW.Console.MessageType.Info)

                # Close the pipe handle
                win32file.CloseHandle(self.pipe_handle)
                Py4GW.Console.Log(module_name, "Named pipe server stopped.", Py4GW.Console.MessageType.Info)
            except pywintypes.error as e:
                Py4GW.Console.Log(module_name, f"Error during cleanup: {e}", Py4GW.Console.MessageType.Error)
            finally:
                # Reset internal state
                self.pipe_handle = None
                self.client_connected = False


# Utility Functions for Embedded Use
def initialize_pipe(server_name):
    """Initialize the pipe server."""
    global server
    if server is None:
        server = NamedPipeServer(pipe_name=server_name)
        server.create_pipe()


def handle_pipe_communication():
    """Handle the pipe communication in the game loop."""
    global server
    if server is not None:
        if not server.client_connected:
            server.wait_for_client()  # Retry connection
        else:
            message = server.receive_message()
            if message:
                server.send_message(f"Echo: {message}")


# GUI Rendering Function
def DrawWindow():
    global module_name, server
    try:
        if PyImGui.begin(module_name):
            PyImGui.text("Onion Pipe Server")
            PyImGui.separator()

            if server is None:
                if PyImGui.button("Start Server"):
                    initialize_pipe("python_to_python")
                    Py4GW.Console.Log(module_name, "Pipe server started.", Py4GW.Console.MessageType.Info)
            else:
                if PyImGui.button("Stop Server"):
                    if server.client_connected:
                        server.handle_disconnect()  # Ensure proper disconnection
                    server.cleanup()  # Cleanup the pipe
                    server = None
                    Py4GW.Console.Log(module_name, "Pipe server stopped.", Py4GW.Console.MessageType.Info)

            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


# Main Loop
def main():
    try:
        DrawWindow()
        if server is not None:
            handle_pipe_communication()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error: {str(e)}", Py4GW.Console.MessageType.Error)
