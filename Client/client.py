import socket
import os
import sys
import time

DEFAULT_PORT = 8080

def client_get(client_socket, file_path, host_name):
    """Handle the GET request to retrieve a file from the server."""
    try:
        request = f"GET {file_path} HTTP/1.1\r\nHost: {host_name}\r\nConnection: close\r\n\r\n"
        client_socket.send(request.encode())

        # Receive the server's response in chunks
        response = b""
        while True:
            part = client_socket.recv(1024)
            if not part:
                break
            response += part

        # Split the response into headers and body
        header, _, body = response.partition(b'\r\n\r\n')

        # Print the response headers for debugging
        print(f"Response Headers:\n{header.decode()}")

        # Check for successful response (HTTP 200 OK)
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
    """Handle the POST request to upload a file to the server."""
    try:
        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            return

        # Read the file content in binary mode
        with open(file_path, "rb") as f:
            file_content = f.read()

        request = (
            f"POST {file_path} HTTP/1.1\r\n"
            f"Host: {host_name}\r\n"
            "Content-Type: application/octet-stream\r\n"
            f"Content-Length: {len(file_content)}\r\n"
            "Connection: close\r\n\r\n"
        ).encode() + file_content  # Append the file content to the request

        client_socket.send(request)

        # Receive the server's response
        response = b""
        while True:
            part = client_socket.recv(1024)
            if not part:
                break
            response += part

        # Split the response into headers and body
        header, _, body = response.partition(b'\r\n\r\n')

        print(f"Response Headers:\n{header.decode()}")
        print(f"Response Body:\n{body.decode()}")
            
    except Exception as e:
        print(f"Error in POST request: {e}")

def main():
    """Main function to read commands from the input file and process them."""
    if len(sys.argv) < 3:
        print("Usage: python my_client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    input_file = "command.txt"  # Always use 'command.txt' as the input file

    try:
        with open(input_file, "r") as f:
            for line in f:
                parts = line.strip().split()  # Split the line into parts
                if len(parts) < 4:
                    print("Error: Invalid command format.")
                    continue

                command, file_path, host_name, port = parts[:4]
                port = int(port)

                # Create a new socket for each command
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((host_name, port))

                if command == "client_get":
                    client_get(client_socket, file_path, host_name)
                elif command == "client_post":
                    client_post(client_socket, file_path, host_name)
                else:
                    print("Error: Unknown command.")

                client_socket.close()
                time.sleep(0.5)  # Small delay to ensure previous request is processed

    except Exception as e:
        print(f"Error establishing connection or processing commands: {e}")

if __name__ == "__main__":
    main()
