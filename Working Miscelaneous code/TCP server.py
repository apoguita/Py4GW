from Py4GWCoreLib import *

module_name = "Hello World!"
server = None
manager = None

def server_thread_function():
    """Function to run the TCP server in a thread."""
    global server
    try:
        if server:
            server.handle_clients()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Server thread error: {e}", Py4GW.Console.MessageType.Error)
    finally:
        if server:
            server.cleanup()

def DrawWindow():
    global module_name, manager, server
    try:
        if PyImGui.begin(module_name):
            PyImGui.text("TCP Server")
            PyImGui.separator()

            # Button to start the server thread
            if manager is None:
                if PyImGui.button("Start Thread"):
                    manager = MultiThreading()
                    if "server_thread" not in manager.threads:
                        manager.add_thread("server_thread", server_thread_function)
                        manager.start_thread("server_thread")
                        Py4GW.Console.Log(module_name, "Server thread started.", Py4GW.Console.MessageType.Info)

            # Button to start the server
            if manager and server is None:
                if PyImGui.button("Start Server"):
                    server = TCPServer()
                    server.start_server()
                    #Py4GW.Console.Log(module_name, "Server started.", Py4GW.Console.MessageType.Info)

            # Button to stop the server
            if server:
                if PyImGui.button("Stop Server"):
                    server.cleanup()
                    #server = None  # Reset the server instance
                    #Py4GW.Console.Log(module_name, "Server stopped.", Py4GW.Console.MessageType.Info)

            # Button to stop the server thread
            if manager and "server_thread" in manager.threads:
                if PyImGui.button("Stop Thread"):
                    manager.stop_thread("server_thread")
                    #manager = None  # Reset the thread manager
                    #Py4GW.Console.Log(module_name, "Server thread stopped.", Py4GW.Console.MessageType.Info)

            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        DrawWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

