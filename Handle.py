import os
import mimetypes
import re
from FileListPage import send_directory_listing
from Authorization import check_request_auth, add_request_auth
from http_util import parse_http_params, simple_unquote, HttpResponse
from cookies import check_session, create_session

project_path = os.getcwd()
project_path = os.fspath(project_path)
project_path += "/data/"
dir_path = project_path
Authorization_needed = True

http_response = None

def handle_request(client_socket):
    global dir_path
    global http_response
    request_data = client_socket.recv(1024).decode("utf-8")
    # print("request data = ///////////\n" + str(request_data) + "\nrequest data ends///////////")

    if not request_data:
        return

    http_response = HttpResponse()

    method, path, query_params, headers, body = parse_http_params(request_data)
    path = simple_unquote(path) # 转化%20等字符
    print("method = " + str(method))
    print("path = " + str(path))
    print("query_params = " + str(query_params))
    print([h for h in headers if h.startswith('Authorization: Basic')])
    print([h for h in headers if h.startswith('Cookie: ')])
    print([h for h in headers if h.startswith('Content-Length: ')])
    # print("headers = " + str(headers))  
    print('//////////////////////////////////////////////////////////')
    
    if path=="/login":
        handle_login(client_socket, request_data)
        return
    elif path=="/register":
        handle_register(client_socket, request_data)
        return
    elif path.startswith("/web"):
        handle_get(client_socket, path, request_data)
        return
    

    if Authorization_needed:
        username_cookie = check_session(headers)
        if not username_cookie:
            username_auth = check_request_auth(request_data)
            if not username_auth:
                new_head = {'WWW-Authenticate': 'Basic realm="Login Required"'}
                http_response.add_header(new_head)
                http_response.set_response(401, "Unauthorized")
                send_file(client_socket, project_path+"/web/login.html")
                return
            else:
                session_id = create_session(username_auth)
                cookie_head = {'Set-Cookie': f'session_id={session_id}'}
                http_response.add_header(cookie_head)

                
        
    if method == "GET":
        if path.endswith("/"):
            dir_path = project_path + path
        handle_get(client_socket, path, request_data)
    elif method == "POST":
        handle_post(client_socket, dir_path, request_data)
    elif method == "DELETE":
        handle_delete(client_socket, simple_unquote(query_params['file']), dir_path)
    elif method == "HEAD":
        http_response.set_response(200)
        response = http_response.gen_response()
        client_socket.send(response.encode("utf-8"))


def handle_login(client_socket, request_data):
    global http_response
    new_head = {'WWW-Authenticate': 'Basic realm="Login Required"'}
    _, _, _, headers, _ = parse_http_params(request_data)
    username = check_request_auth(request_data)
    if username: # 认证成功
        if not check_session(headers): # 没有cookie则设置cookie
            session_id = create_session(username)
            cookie_head = {'Set-Cookie': f'session_id={session_id}'}
            http_response.add_header(cookie_head)
            http_response.set_response(200, "Login Successful!")
        else:
            http_response.set_response(200, "Login Successful!")
    else:
        # 没有凭证
        http_response.add_header(new_head)
        http_response.set_response(401, "Unauthorized")

    response = http_response.gen_response()
    client_socket.send(response.encode("utf-8"))
    
def handle_register(client_socket, request_data):
    global http_response
    new_head = {'WWW-Authenticate': 'Basic realm="Login Required"'}
    _, _, _, headers, _ = parse_http_params(request_data)
    new_username = add_request_auth(request_data)
    if new_username:
        session_id = create_session(new_username)
        cookie_head = {'Set-Cookie': f'session_id={session_id}'}
        http_response.add_header(cookie_head)
        http_response.set_response(200, "Register Successful!")
    else:
        http_response.add_header(new_head)
    
    response = http_response.gen_response()
    client_socket.send(response.encode("utf-8"))

def handle_get(client_socket, path, request_data):
    global http_response
    path_ = path
    path = project_path + path
    if os.path.isfile(path):
        send_file(client_socket, path)
    elif os.path.isdir(path):
        if not path.endswith("/"):
            # Redirect to the directory path with a trailing slash
            loacation_head = {'Location': path_ + '/'}
            http_response.add_header(loacation_head)
            http_response.set_response(301)
            response = http_response.gen_response()
            # response = f"HTTP/1.1 301 Moved Permanently\r\nLocation: {path_}/\r\n\r\n"
            client_socket.send(response.encode("utf-8"))
        else:
            # Display directory listing
            send_directory_listing(client_socket, path, request_data, http_response)
    else:
        send_not_found(client_socket)


def handle_post(client_socket, dir_path, request_data):
    global http_response
    try:
        # Read the headers to find the content length
        headers, _, _ = request_data.partition("\r\n\r\n")
        headers_dict = dict(line.split(": ", 1) for line in headers.split("\r\n")[1:])
        content_length = int(headers_dict.get('Content-Length', 0))

        # Read the content in chunks
        chunk_size = 1024
        received_content = b''
        print("content_length = " + str(content_length))
        while len(received_content) < content_length:
            print(min(chunk_size, content_length - len(received_content)))
            chunk = client_socket.recv(min(chunk_size, content_length - len(received_content)))
            if not chunk:
                raise ValueError("Connection closed unexpectedly")

            received_content += chunk
            print("received_content length = " + str(len(received_content)))
            # print(chunk.decode("utf-8"))

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
        http_response.set_response(200, "File uploaded!")
        # response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 17\r\n\r\nFile uploaded!\r\n"
        response = http_response.gen_response()
        client_socket.send(response.encode("utf-8"))

    except Exception as e:
        # Handle errors and send an appropriate response
        print("Upload error message:" + str(e))
        error_message = f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: {len(str(e))}\r\n\r\n{str(e)}\r\n"
        client_socket.send(error_message.encode("utf-8"))


def handle_delete(client_socket, relative_path, dir_path):
    global http_response
    try:
        print("relative_path = " + str(relative_path))
        file_path = os.path.join(dir_path, relative_path.lstrip('/'))

        # Ensure that the file is within the project_path to avoid security risks
        if os.path.commonprefix([os.path.abspath(file_path), os.path.abspath(project_path)]) != os.path.abspath(
                project_path):
            raise ValueError("Invalid file path")

        print(f"Deleting file: {os.path.abspath(file_path)}")  # Corrected output line
        os.remove(file_path)
        http_response.set_response(200, "Deleted")
        # response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 10\r\n\r\nDeleted\r\n"
        response = http_response.gen_response()
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
    global http_response
    with open(file_path, "rb") as file:
        content = file.read()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        http_response.set_content_type(content_type)
        http_response.set_response(200)
        # response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n"
        response_headers = http_response.gen_response_header(len(content))
        client_socket.send(response_headers.encode("utf-8") + content)


def send_not_found(client_socket):
    global http_response
    http_response.set_response(404, "Not Found")
    # response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nNot Found\r\n"
    response = http_response.gen_response()
    client_socket.send(response.encode("utf-8"))
