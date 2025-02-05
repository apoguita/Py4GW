from Py4GWCoreLib import *
import socket
import threading

module_name = "TCP Server"
server = None
server_thread = None

global_enter_challenge = False

class TCPServer:
    global global_enter_challenge
    def __init__(self, host='127.0.0.1', port=12345, buffer_size=4096):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.retry_timer = Timer()
        self.retry_timer.Start()
        self.running = False
        self.lock = threading.Lock()

    def start_server(self):
        """Start the TCP server and bind to the specified host and port."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)  # Allow only one connection at a time
            self.running = True
            Py4GW.Console.Log(module_name, f"Server started and listening on {self.host}:{self.port}", Py4GW.Console.MessageType.Info)
        except socket.error as e:
            Py4GW.Console.Log(module_name, f"Error starting server: {e}", Py4GW.Console.MessageType.Error)
            self.cleanup()

    def wait_for_client(self):
        """Attempt to connect to a client using retry logic based on a timer."""
        if not self.client_socket and self.retry_timer.HasElapsed(500):  # Retry every 500ms
            try:
                self.server_socket.settimeout(0.1)  # Non-blocking wait
                self.client_socket, self.client_address = self.server_socket.accept()
                Py4GW.Console.Log(module_name, f"Client connected from {self.client_address}", Py4GW.Console.MessageType.Success)
                self.retry_timer.Reset()
            except socket.timeout:
                pass  # No client connected yet
            except socket.error as e:
                Py4GW.Console.Log(module_name, f"Error while waiting for client: {e}", Py4GW.Console.MessageType.Warning)

    def handle_client(self):
        global global_enter_challenge
        """Handle communication with the client."""
        while self.running:
            with self.lock:
                if self.client_socket:
                    try:
                        data = self.client_socket.recv(self.buffer_size)
                        if data:
                            message = data.decode()
                            Py4GW.Console.Log(module_name, f"Received: {message}", Py4GW.Console.MessageType.Info)
                            self.send_message(f"Echo: {message}")
                            
                            if message == "GET_AGENT_ID":
                                agent_id = str(Player.GetAgentID())  # Obtain agent ID from Py4GW
                                self.send_message(agent_id)  # Send agent ID to AutoIt client
                            if message == "ENTER_CHALLENGE_MISSION":
                                global_enter_challenge = True
                                self.send_message("SUCCESS") 
                            else:
                                self.send_message(f"Echo: {message}")  # Default echo response


                        else:
                            Py4GW.Console.Log(module_name, "Client disconnected.", Py4GW.Console.MessageType.Info)
                            self.cleanup_client()
                            break
                    except socket.error as e:
                        Py4GW.Console.Log(module_name, f"Error receiving message: {e}", Py4GW.Console.MessageType.Error)
                        break

    def send_message(self, message):
        """Send a message to the client."""
        if self.client_socket:
            try:
                self.client_socket.sendall(message.encode())
                Py4GW.Console.Log(module_name, f"Sent: {message}", Py4GW.Console.MessageType.Info)
            except socket.error as e:
                Py4GW.Console.Log(module_name, f"Error sending message: {e}", Py4GW.Console.MessageType.Error)
                self.cleanup_client()

    def cleanup_client(self):
        """Clean up the client connection."""
        with self.lock:
            if self.client_socket:
                try:
                    self.client_socket.close()
                    Py4GW.Console.Log(module_name, "Client connection closed.", Py4GW.Console.MessageType.Info)
                except socket.error as e:
                    Py4GW.Console.Log(module_name, f"Error closing client connection: {e}", Py4GW.Console.MessageType.Warning)
                finally:
                    self.client_socket = None
                    self.client_address = None

    def cleanup(self):
        """Clean up the server."""
        self.cleanup_client()
        if self.server_socket:
            try:
                self.server_socket.close()
                Py4GW.Console.Log(module_name, "Server socket closed.", Py4GW.Console.MessageType.Info)
            except socket.error as e:
                Py4GW.Console.Log(module_name, f"Error closing server socket: {e}", Py4GW.Console.MessageType.Error)
            finally:
                self.server_socket = None
                self.running = False


# Server Thread Function
def server_thread_function():
    global server
    try:
        while server.running:
            try:
                server.server_socket.settimeout(0.5)  # Ensure accept() times out
                server.wait_for_client()
                if server.client_socket:
                    server.handle_client()
            except socket.timeout:
                continue  # Timeout allows us to check the running flag
            except Exception as e:
                if server.running:  # Only log errors if the server is supposed to be running
                    Py4GW.Console.Log(module_name, f"Server thread error: {e}", Py4GW.Console.MessageType.Warning)
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected server thread error: {e}", Py4GW.Console.MessageType.Error)
    finally:
        Py4GW.Console.Log(module_name, "Server thread exiting.", Py4GW.Console.MessageType.Info)




# Utility Functions
def initialize_server():
    """Initialize the TCP server in a separate thread."""
    global server, server_thread
    if server is None:
        server = TCPServer()
        server.start_server()

    if server_thread is None or not server_thread.is_alive():
        server_thread = threading.Thread(target=server_thread_function, daemon=True)
        server_thread.start()
        Py4GW.Console.Log(module_name, "Server thread started.", Py4GW.Console.MessageType.Info)


def stop_server():
    """Stop the TCP server and its thread."""
    global server, server_thread
    if server:
        server.running = False
        # Closing server socket interrupts accept()
        try:
            if server.server_socket:
                server.server_socket.close()
                Py4GW.Console.Log(module_name, "Server socket closed.", Py4GW.Console.MessageType.Info)
        except Exception as e:
            Py4GW.Console.Log(module_name, f"Error closing server socket: {e}", Py4GW.Console.MessageType.Warning)
        server.cleanup()
        server = None

    if server_thread and server_thread.is_alive():
        server_thread.join(timeout=2)  # Wait for the thread to exit
        if server_thread.is_alive():
            Py4GW.Console.Log(module_name, "Forcefully terminating server thread.", Py4GW.Console.MessageType.Warning)
            server_thread = None  # Allow the program to proceed regardless



# GUI Rendering Function
def DrawWindow():
    global module_name, server_thread, global_enter_challenge
    try:
        if PyImGui.begin(module_name):
            PyImGui.text("TCP Server")
            PyImGui.separator()

            if server is None:
                if PyImGui.button("Start Server"):
                    initialize_server()
                    Py4GW.Console.Log(module_name, "Server started.", Py4GW.Console.MessageType.Info)
            else:
                if PyImGui.button("Stop Server"):
                    stop_server()
                    Py4GW.Console.Log(module_name, "Server stopped.", Py4GW.Console.MessageType.Info)
                    
            if global_enter_challenge:
                Map.EnterChallenge()
                global_enter_challenge = False
                Py4GW.Console.Log(module_name, f"Entered Challenge: {str(e)}", Py4GW.Console.MessageType.Info)

            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


# Main Loop
def main():
    try:
        DrawWindow()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error: {str(e)}", Py4GW.Console.MessageType.Error)
