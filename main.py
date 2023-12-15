import socket
import os
import mimetypes
import urllib.parse
from urllib.parse import urlparse, unquote

project_path = "/Users/jrx/课程资料/CS305-Computer Network/Project"
dir_path = project_path

def handle_request(client_socket):
    global dir_path
    request_data = client_socket.recv(1024).decode("utf-8")

    print("request data = " + str(request_data) + "\nrequest data ends")

    if not request_data:
        return

    method, path, _ = request_data.split(" ", 2)
    path = urllib.parse.unquote(path)
    print("method = " + str(method) + " and dir_path = " + dir_path)

    if method == "GET":
        dir_path = project_path + path
        handle_get(client_socket, path)
    elif method == "POST":
        handle_post(client_socket, request_data, dir_path)
    elif method == "DELETE":
        handle_delete(client_socket, path, dir_path)


def handle_get(client_socket, path):
    path = project_path + path
    print("Enter path: " + path)
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
            <script>
                function deleteFile(filePath) {
                    if (confirm("确认删除文件？")) {
                        // Send an asynchronous request to the server to delete the file
                        fetch(`/delete?file=${encodeURIComponent(filePath)}`, {
                            method: 'DELETE'
                        })
                        .then(response => {
                            if (response.ok) {
                                alert("文件已删除！");
                                // Optionally, you can reload the page or update the file listing
                                location.reload();
                            } else {
                                alert("删除文件失败！");
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert("发生错误，无法删除文件！");
                        });
                    }
                }
            </script>

        </head>
        <body>
            <h1>File Listing</h1>
            <form enctype="multipart/form-data" method="post" action="/">
                <input name="file" type="file"/>
                <input type="submit" value="upload"/>
            </form>
            <ul>
    """
    content += f'<li><a href="{urllib.parse.quote("..")}">返回上一级</a></li>'

    for file in file_list:
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            file += "/"
        content += f'<li><a href="{urllib.parse.quote(file)}">{file}</a> <button onclick="deleteFile(\'{urllib.parse.quote(file)}\')">Delete</button></li>'

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


def handle_post(client_socket, request_data, dir_path):
    try:
        _, _, content = request_data.partition("\r\n\r\n")

        # Get the current directory path from the request data
        _, path, _ = request_data.split(" ", 2)
        path = urllib.parse.unquote(path)
        current_dir = dir_path
        print("current_dir: " + current_dir)

        # Ensure that the current directory is within the project_path to avoid security risks
        if os.path.commonprefix([os.path.abspath(current_dir), os.path.abspath(project_path)]) != os.path.abspath(project_path):
            raise ValueError("Invalid directory path")

        filename = os.path.join(current_dir, "uploaded_file.txt")

        with open(filename, "wb") as file:
            file.write(content.encode("utf-8"))

        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 17\r\n\r\nFile uploaded!\r\n"
        client_socket.send(response.encode("utf-8"))

    except Exception as e:
        print(f"Error handling POST request: {e}")
        response = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\nContent-Length: 27\r\n\r\nInternal Server Error\r\n"
        client_socket.send(response.encode("utf-8"))



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
        if os.path.commonprefix([os.path.abspath(file_path), os.path.abspath(project_path)]) != os.path.abspath(project_path):
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
