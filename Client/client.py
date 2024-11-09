import socket
import os
import sys
import time

# Default port for server connection
DEFAULT_PORT = 8080

def client_get(client_socket, file_path, host_name):
    """
    Handle the GET request to retrieve a file from the server.

    Args:
        client_socket (socket): The socket object for communication with the server.
        file_path (str): Path of the file to be retrieved.
        host_name (str): Hostname of the server.
    """
    try:
        # Construct the GET request
        request = f"GET {file_path} HTTP/1.1\r\nHost: {host_name}\r\nConnection: keep-alive\r\n\r\n"
        client_socket.send(request.encode())

        # Receive response in chunks and accumulate
        response = b""
        while True:
            chunk = client_socket.recv(1024)
            response += chunk
            if len(chunk) < 1024:  # Check if end of response is reached
                break

        # Separate headers and body in the response
        header, _, body = response.partition(b'\r\n\r\n')
        
        # Display headers for debugging
        print(f"Response Headers:\n{header.decode()}")

        # Check for successful response (HTTP 200 OK) and save file
        if b"200 OK" in header:
            file_name = os.path.basename(file_path)
            with open(file_name, "wb") as f:
                f.write(body)
            print(f"File '{file_name}' saved successfully.")
        else:
            print("Error: Could not retrieve file.")
            
    except Exception as e:
        print(f"Error in GET request: {e}")

def client_post(client_socket, file_path, host_name):
    """
    Handle the POST request to upload a file to the server.

    Args:
        client_socket (socket): The socket object for communication with the server.
        file_path (str): Path of the file to be uploaded.
        host_name (str): Hostname of the server.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            return

        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Construct the POST request including headers and file content
        request = (
            f"POST {file_path} HTTP/1.1\r\n"
            f"Host: {host_name}\r\n"
            "Content-Type: application/octet-stream\r\n"
            f"Content-Length: {len(file_content)}\r\n"
            "Connection: keep-alive\r\n\r\n"
        ).encode() + file_content

        client_socket.send(request)

        # Receive response in chunks and accumulate
        response = b""
        while True:
            chunk = client_socket.recv(1024)
            response += chunk
            if len(chunk) < 1024:  # Check if end of response is reached
                break

        # Separate headers and body in the response
        header, _, body = response.partition(b'\r\n\r\n')

        # Display headers and body for debugging
        print(f"Response Headers:\n{header.decode()}")
        print(f"Response Body:\n{body.decode()}")
            
    except Exception as e:
        print(f"Error in POST request: {e}")

def main():
    """
    Main function to read commands from the input file and process them.
    """
    # Check for required arguments
    if len(sys.argv) < 3:
        print("Usage: python my_client.py <server_ip> <server_port>")
        sys.exit(1)

    # Read server IP and port from command line arguments
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    # Input file with commands
    input_file = "commands.txt"

    try:
        with open(input_file, "r") as f:
            # Initialize socket connection to the server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, server_port))
            
            for line in f:
                print()
                parts = line.strip().split()  # Parse command line

                # Validate command format
                if len(parts) < 4:
                    print("Error: Invalid command format.")
                    continue

                # Extract command, file path, hostname, and port from the line
                command, file_path, host_name, port = parts[:4]
                port = int(port)

                # Execute the appropriate command
                if command == "client_get":
                    client_get(client_socket, file_path, host_name)
                elif command == "client_post":
                    client_post(client_socket, file_path, host_name)
                else:
                    print("Error: Unknown command.")

                # Small delay to ensure processing of the previous request
                time.sleep(0.5)

            # Send final close connection request
            request = f"GET '' HTTP/1.1\r\nHost: {host_name}\r\nConnection: close\r\n\r\n"
            client_socket.send(request.encode())
        
    except Exception as e:
        print(f"Error establishing connection or processing commands: {e}")

if __name__ == "__main__":
    main()
