

import socket
import threading
import os

CONTENT_TYPES = {
    ".html": "text/html",
    ".txt": "text/plain",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png"
}

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
    while True:
        try:
            data = receive_full_request(client_socket)
            if not data:
                break

            headers, _, body = data.partition(b'\r\n\r\n')
            headers_text = headers.decode()

            request_line = headers_text.splitlines()[0]
            method, path, _ = request_line.split()

            if method == 'GET':
                handle_get(client_socket, path)
            elif method == 'POST':
                handle_post(client_socket, path, body)
            else:
                handle_unsupported_method(client_socket)

            # Check if client requested connection close
            if "Connection: close" in headers_text:
                break

        except socket.timeout:
            print("Connection closed due to timeout")
            break
        except Exception as e:
            print(f"Error: {e}")
            break
    client_socket.close()

def receive_full_request(client_socket):
    """Receive full HTTP request, accounting for Content-Length if present."""
    client_socket.settimeout(20)
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

def handle_unsupported_method(client_socket):
    response_body = "Method Not Allowed"
    response_headers = [
        "HTTP/1.1 405 Method Not Allowed",
        "Connection: close",
        f"Content-Length: {len(response_body)}",
        "Content-Type: text/plain",
        "\r\n"
    ]
    response = "\r\n".join(response_headers).encode() + response_body.encode()
    client_socket.sendall(response)
    
def handle_bad_request(client_socket):
    """Handle bad requests by sending a 400 Bad Request response."""
    
    send_response(client_socket, "Bad Request", status="400 Bad Request")

if __name__ == "__main__":
    # Run the server on localhost and port 8080
    start_server(host='localhost', port=8080)
     