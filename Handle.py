import socket
import os
import mimetypes
import re
import urllib.parse
from FileListPage import send_directory_listing
from urllib.parse import urlparse, unquote

project_path = "/Users/jrx/课程资料/CS305-Computer Network/Project"
dir_path = project_path
def handle_request(client_socket):
    global dir_path
    request_data = client_socket.recv(1024).decode("utf-8")

    print("request data = ///////////\n" + str(request_data) + "\nrequest data ends///////////")

    if not request_data:
        return

    method, path, _ = request_data.split(" ", 2)
    path = urllib.parse.unquote(path)

    if method == "GET":
        if path.endswith("/"):
            dir_path = project_path + path
        print("dir_path = " + dir_path)
        handle_get(client_socket, path, request_data)
    elif method == "POST":
        handle_post(client_socket, dir_path, request_data)
    elif method == "DELETE":
        handle_delete(client_socket, path, dir_path)


def handle_get(client_socket, path, request_data):
    path = project_path + path
    if os.path.isfile(path):
        send_file(client_socket, path)
    elif os.path.isdir(path):
        if not path.endswith("/"):
            # Redirect to the directory path with a trailing slash
            response = f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path}/\r\n\r\n"
            client_socket.send(response.encode("utf-8"))
        else:
            # Display directory listing
            send_directory_listing(client_socket, path, request_data)
    else:
        send_not_found(client_socket)

def handle_post(client_socket, dir_path, request_data):
    try:
        # Read the headers to find the content length
        headers, _, _ = request_data.partition("\r\n\r\n")
        headers_dict = dict(line.split(": ", 1) for line in headers.split("\r\n")[1:])
        content_length = int(headers_dict.get('Content-Length', 0))

        # Read the content in chunks
        chunk_size = 1024
        received_content = b''

        while len(received_content) < content_length:
            chunk = client_socket.recv(min(chunk_size, content_length - len(received_content)))
            if not chunk:
                raise ValueError("Connection closed unexpectedly")

            received_content += chunk

        # Extract the file content from the multipart form data
        match = re.search(b'\r\n\r\n(.+?)\r\n--', received_content, re.DOTALL)
        if not match:
            raise ValueError("File content not found in multipart form data")

        file_content = match.group(1)

        # Extract the filename from the first part of the content
        filename_match = re.search(b'filename="([^"]+)"', received_content)
        if not filename_match:
            raise ValueError("Filename not found in multipart form data")

        # Construct the full file path including the directory path
        filename = os.path.join(dir_path, filename_match.group(1).decode("utf-8"))

        print("Upload file: " + str(filename))

        # Create a file with the specified filename and content
        with open(filename, "wb") as file:
            file.write(file_content)

        # Send a response back to the client
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 17\r\n\r\nFile uploaded!\r\n"
        client_socket.send(response.encode("utf-8"))

    except Exception as e:
        # Handle errors and send an appropriate response
        print("Upload error message:" + str(e))
        error_message = f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: {len(str(e))}\r\n\r\n{str(e)}\r\n"
        client_socket.send(error_message.encode("utf-8"))


def handle_delete(client_socket, path, dir_path):
    try:
        query_params = urlparse(path).query
        print("path = " + path)
        print("query_params" + str(query_params))
        file_param = dict(qc.split("=") for qc in query_params.split("&"))
        relative_path = unquote(file_param.get('file', ''))
        print("relative_path = " + str(relative_path))
        file_path = os.path.join(dir_path, relative_path.lstrip('/'))

        # Ensure that the file is within the project_path to avoid security risks
        if os.path.commonprefix([os.path.abspath(file_path), os.path.abspath(project_path)]) != os.path.abspath(
                project_path):
            raise ValueError("Invalid file path")

        print(f"Deleting file: {os.path.abspath(file_path)}")  # Corrected output line
        os.remove(file_path)
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 10\r\n\r\nDeleted\r\n"
        client_socket.send(response.encode("utf-8"))
    except FileNotFoundError:
        send_not_found(client_socket)
    except ValueError:
        response = "HTTP/1.1 403 Forbidden\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nForbidden\r\n"
        client_socket.send(response.encode("utf-8"))
    except Exception as e:
        print(f"Error deleting file: {e}")
        response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: 21\r\n\r\nInternal Server Error\r\n"
        client_socket.send(response.encode("utf-8"))

def send_file(client_socket, file_path):
    with open(file_path, "rb") as file:
        content = file.read()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n"
        client_socket.send(response_headers.encode("utf-8") + content)

def send_not_found(client_socket):
    response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nNot Found\r\n"
    client_socket.send(response.encode("utf-8"))