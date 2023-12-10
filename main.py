import socket
import os
import mimetypes
import urllib.parse

def handle_request(client_socket):
    request_data = client_socket.recv(1024).decode("utf-8")

    if not request_data:
        return

    method, path, _ = request_data.split(" ", 2)
    path = urllib.parse.unquote(path)

    if method == "GET":
        handle_get(client_socket, path)
    elif method == "POST":
        handle_post(client_socket, request_data)

def handle_get(client_socket, path):
    if os.path.isfile(path):
        send_file(client_socket, path)
    elif os.path.isdir(path):
        if not path.endswith("/"):
            # Redirect to the directory path with a trailing slash
            response = f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path}/\r\n\r\n"
            client_socket.send(response.encode("utf-8"))
        else:
            # Display directory listing
            send_directory_listing(client_socket, path)
    else:
        send_not_found(client_socket)

def send_file(client_socket, file_path):
    with open(file_path, "rb") as file:
        content = file.read()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n"
        client_socket.send(response_headers.encode("utf-8") + content)

def send_directory_listing(client_socket, dir_path):
    file_list = os.listdir(dir_path)
    content = """
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body>
            <h1>File Listing</h1>
            <form enctype="multipart/form-data" method="post" action="/">
                <input name="file" type="file"/>
                <input type="submit" value="upload"/>
            </form>
            <ul>
    """

    for file in file_list:
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            file += "/"
        content += f'<li><a href="{urllib.parse.quote(file)}">{file}</a></li>'

    content += """
            </ul>
        </body>
        </html>
    """

    content_encoded = content.encode("utf-8")
    response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(content_encoded)}\r\n\r\n"
    client_socket.send(response_headers.encode('utf-8') + content_encoded)

def send_not_found(client_socket):
    response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nNot Found\r\n"
    client_socket.send(response.encode("utf-8"))

def handle_post(client_socket, request_data):
    # Parse the request_data to get the file content and file name
    # (similar to the original code's deal_post_data function)
    # For simplicity, this example assumes that the file content is immediately following the headers.
    _, _, content = request_data.partition("\r\n\r\n")
    save_path = "uploads"
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    filename = os.path.join(save_path, "uploaded_file.txt")

    with open(filename, "wb") as file:
        file.write(content.encode("utf-8"))

    response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 17\r\n\r\nFile uploaded!\r\n"
    client_socket.send(response.encode("utf-8"))

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8000))
    server_socket.listen(5)
    print("Server listening on port 8000...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        handle_request(client_socket)
        client_socket.close()


if __name__ == "__main__":
    main()
