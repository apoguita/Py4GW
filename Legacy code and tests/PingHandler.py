# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import traceback    #traceback to log stack traces
# End Necessary Imports
import Py4GWcorelib as CoreLib

module_name = "Ping Handler DEMO"
ping_handler = Py4GW.PingHandler()

def DrawTextWithTitle(title, text_content, lines_visible=10):
    """
    Function to display a title and multi-line text in a scrollable and configurable area.
    Width is based on the main window's width with a margin.
    Height is based on the number of lines_visible.
    """
    margin = 20
    max_lines = 10
    line_padding = 4  # Add a bit of padding for readability

    # Display the title first
    PyImGui.text(title)

    # Get the current window size and adjust for margin to calculate content width
    window_width = PyImGui.get_window_size()[0]
    content_width = window_width - margin
    text_block = text_content + "\n" + Py4GW.Console.GetCredits()

    # Split the text content into lines by newline
    lines = text_block.split("\n")
    total_lines = len(lines)

    # Limit total lines to max_lines if provided
    if max_lines is not None:
        total_lines = min(total_lines, max_lines)

    # Get the line height from ImGui
    line_height = PyImGui.get_text_line_height()
    if line_height == 0:
        line_height = 10  # Set default line height if it's not valid

    # Add padding between lines and calculate content height based on visible lines
    content_height = (lines_visible * line_height) + ((lines_visible - 1) * line_padding)

    # Set up the scrollable child window with dynamic width and height
    if PyImGui.begin_child(f"ScrollableTextArea_{title}", size=(content_width, content_height), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        # Get the scrolling position and window size for visibility checks
        scroll_y = PyImGui.get_scroll_y()
        scroll_max_y = PyImGui.get_scroll_max_y()
        window_size_y = PyImGui.get_window_size()[1]
        window_pos_y = PyImGui.get_cursor_pos_y()

        # Display each line only if it's visible based on scroll position
        for index, line in enumerate(lines):
            # Calculate the Y position of the line based on index
            line_start_y = window_pos_y + (index * (line_height + line_padding))

            # Calculate visibility boundaries
            line_end_y = line_start_y + line_height

            # Skip rendering if the line is above or below the visible area
            if line_end_y < scroll_y or line_start_y > scroll_y + window_size_y:
                continue

            # Render the line if it's within the visible scroll area
            PyImGui.text_wrapped(line)
            PyImGui.spacing()  # Add spacing between lines for better readability

        # End the scrollable child window
        PyImGui.end_child()



def DrawWindow():
    global module_name, ping_handler
    try:
        description = "This is a test for the PingHandler class \nIt creates a callback and stores basic ping statistics."


        width, height = 400, 500
        PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(module_name):

            DrawTextWithTitle("ATTENTION", description,5)

            current_ping = ping_handler.GetCurrentPing()
            min_ping = ping_handler.GetMinPing()
            max_ping = ping_handler.GetMaxPing()
            avg_ping = ping_handler.GetAveragePing()

            # Display the ping statistics in a table format
            headers = ["Ping Statistics"]
            data = [f"Current Ping: {current_ping} ms",
                    f"Min Ping: {min_ping} ms",
                    f"Max Ping: {max_ping} ms",
                    f"Average Ping: {avg_ping} ms"]

            CoreLib.ImGui.table("Ping Info Table", headers, data)

            PyImGui.end()


    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in PerformTask: {str(e)}", Py4GW.Console.MessageType.Error)
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
