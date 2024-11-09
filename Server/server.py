import socket
import threading
import os

# Dictionary to map file extensions to their corresponding content types
CONTENT_TYPES = {
    ".html": "text/html",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png"
}

# Global variables for managing active connections
active_connections = 0
connection_lock = threading.Lock()  # Lock for thread-safe access to active_connections

def calculate_timeout():
    """Calculate the timeout duration based on the number of active connections."""
    global active_connections
    if active_connections < 5:
        return 20  # Long timeout if under low load
    elif active_connections < 10:
        return 10  # Medium timeout if load is moderate
    else:
        return 5   # Short timeout if the server is busy

def start_server(host='localhost', port=8080):
    """Start the HTTP server to accept incoming connections."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server started on {host}:{port}")
    
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

def handle_client(client_socket):
    """Handle incoming client connections and process requests."""
    global active_connections
    with connection_lock:  # Increment active connection count
        active_connections += 1

    try:
        while True:
            data = receive_full_request(client_socket)
            if not data:
                break

            # Separate headers and body
            headers, _, body = data.partition(b'\r\n\r\n')
            headers_text = headers.decode(errors="replace")  # Decode headers only for readability

            # Print the request headers
            print()
            print("Received request headers:")
            print(headers_text)

            request_line = headers_text.splitlines()[0]
            method, path, _ = request_line.split()

            if method == 'GET':
                handle_get(client_socket, path)
            else:
                handle_post(client_socket, path, body)

            # Check if client requested connection close
            if "Connection: close" in headers_text:
                break

    except socket.timeout:
        print("Connection closed due to timeout")
    finally:
        # Decrement active connection count and close the socket
        with connection_lock:
            active_connections -= 1
        client_socket.close()
  
def receive_full_request(client_socket):
    """Receive full HTTP request, accounting for Content-Length if present."""
    client_socket.settimeout(calculate_timeout())
    data = b""
    while True:
        part = client_socket.recv(1024)
        data += part
        if b'\r\n\r\n' in data:
            headers = data.split(b'\r\n\r\n', 1)[0]
            headers_text = headers.decode()
            if "Content-Length" in headers_text:
                content_length = int(headers_text.split("Content-Length: ")[1].split("\r\n")[0])
                while len(data) < len(headers) + 4 + content_length:
                    data += client_socket.recv(1024)
            break
    return data

def handle_get(client_socket, path):
    filepath = path.lstrip("/")
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            content = f.read()
        extension = os.path.splitext(filepath)[1]
        content_type = CONTENT_TYPES.get(extension, "application/octet-stream")
        
        response_headers = [
            "HTTP/1.1 200 OK",
            "Connection: keep-alive",
            f"Content-Length: {len(content)}",
            f"Content-Type: {content_type}",
            "\r\n"
        ]
        response = "\r\n".join(response_headers).encode() + content
    else:
        response_headers = [
            "HTTP/1.1 404 Not Found",
            "Connection: close",
            "Content-Length: 13",
            "Content-Type: text/plain",
            "\r\n"
        ]
        response = "\r\n".join(response_headers).encode() + b"File Not Found"
    
    client_socket.sendall(response)

def handle_post(client_socket, path, body):
    filepath = path.lstrip("/")
    with open(filepath, 'wb') as f:
        f.write(body)

    response_body = f"File '{filepath}' saved successfully."
    response_headers = [
        "HTTP/1.1 200 OK",
        "Connection: keep-alive",
        f"Content-Length: {len(response_body)}",
        "Content-Type: text/plain",
        "\r\n"
    ]
    response = "\r\n".join(response_headers).encode() + response_body.encode()
    client_socket.sendall(response)

if __name__ == "__main__":
    # Run the server on localhost and port 8080
    start_server(host='localhost', port=8080)
