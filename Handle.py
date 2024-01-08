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
current_user = None
def handle_request(client_socket, request_data):
    global dir_path
    global http_response
    global current_user
    # request_data = client_socket.recv(1024).decode("utf-8")

    if not request_data:
        return

    http_response = HttpResponse()

    method, path, query_params, headers, body = parse_http_params(request_data)
    path = simple_unquote(path) # 转化%20等字符
    print("method = " + str(method))
    print("path = " + str(path))
    print("query_params = " + str(query_params))
    print([h for h in headers if h.startswith('Authorization: ')])
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
                modified_send_file(client_socket, project_path+"/web/login.html", headers)
                return
            else:
                current_user = username_auth
                session_id = create_session(username_auth)
                cookie_head = {'Set-Cookie': f'session_id={session_id}'}
                http_response.add_header(cookie_head)
        else:
            current_user = username_cookie

    if current_user == "1":
        current_user = "admin"
    
    # check authorization of user path when upload or delete
    if path == "/upload" or path == "/delete":
        target_path = simple_unquote(query_params['path'])
        if not target_path.startswith(project_path):
            target_path = project_path + target_path
        target_path = os.path.normpath(target_path)
        print("target_path = " + str(target_path))
        if current_user != "admin":
            if not (target_path.startswith(project_path + current_user + "/")) :
                http_response.set_response(403, "Forbidden")
                response = http_response.gen_response()
                client_socket.send(response.encode("utf-8"))
                return
            
    if method == "GET":
        if path.endswith("/"):
            dir_path = project_path + path
        handle_get(client_socket, path, request_data)
    elif method == "POST" and path == "/upload":
        handle_post(client_socket, target_path, request_data)
    elif method == "POST" and path == "/delete":
        handle_delete(client_socket, target_path)
    elif method == "HEAD":
        http_response.set_response(200)
        response = http_response.gen_response()
        client_socket.send(response.encode("utf-8"))
    else:
        http_response.set_response(405, "Method Not Allowed")
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
    _, _, query_params, headers, _ = parse_http_params(request_data)
    if os.path.isfile(path):
        chunk = query_params.get('chunked', 0)
        if chunk == '1':
            print("send file chunked")
            send_file_chunked(client_socket, path)
        else:
            modified_send_file(client_socket, path, headers)
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
        _, _, _, headers, body = parse_http_params(request_data)
        headers_dict = dict(line.split(": ", 1) for line in headers)
        content_length = int(headers_dict.get('Content-Length', 0))

        # 确定分隔符
        content_type = headers_dict.get('Content-Type', '')
        boundary = content_type.split("boundary=")[-1]
        if not boundary:
            raise ValueError("Multipart boundary not found")

        # 读取所有数据
        received_content = body.encode("utf-8")
        while len(received_content) < content_length:
            chunk = client_socket.recv(min(1024, content_length - len(received_content)))
            if not chunk:
                raise ValueError("Connection closed unexpectedly")
            received_content += chunk

        # 处理每个部分
        parts = received_content.split(("--" + boundary).encode())
        for part in parts:
            if part:
                process_multipart_part(part, dir_path)

        # 发送响应
        http_response.set_response(200, "File uploaded!")
        # response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 17\r\n\r\nFile uploaded!\r\n"
        response = http_response.gen_response()
        client_socket.send(response.encode("utf-8"))

    except Exception as e:
        print("Upload error message:" + str(e))
        error_message = f"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: {len(str(e))}\r\n\r\n{str(e)}\r\n"
        client_socket.send(error_message.encode("utf-8"))

def process_multipart_part(part, dir_path):
    headers, _, content = part.partition(b'\r\n\r\n')
    header_lines = headers.decode('utf-8').split('\r\n')
    header_dict = {}
    for line in header_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            header_dict[key.strip()] = value.strip()

    
    content_disposition = header_dict.get('Content-Disposition', '')
    if 'filename="' in content_disposition:
        # 提取文件名
        filename = content_disposition.split('filename="')[-1].split('"')[0]
        file_path = os.path.join(dir_path, filename)

        # 写入文件
        with open(file_path, 'wb') as file:
            file.write(content)

        print(f"File uploaded: {file_path}")

def handle_delete(client_socket, file_path):
    global http_response
    try:
        

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
    print("send file: " + str(file_path))   
    with open(file_path, "rb") as file:
        content = file.read()
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        http_response.set_content_type(content_type)
        # response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(content)}\r\n\r\n"
        response_headers = http_response.gen_response_header(len(content))
        client_socket.send(response_headers.encode("utf-8") + content)
        
def send_file_chunked(client_socket, file_path):
    global http_response
    print("send file: " + str(file_path))
    
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    http_response.set_content_type(content_type)
    # 设置为 chunked 传输
    http_response.add_header({'Transfer-Encoding':'chunked'})
    # 生成响应头
    response_headers = http_response.gen_response_header()
    client_socket.send(response_headers.encode("utf-8"))

    # 发送文件内容
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(1024)  # 读取最多 1024 字节
            if not chunk:
                break  # 文件结束
            # 发送块大小和数据
            size_str = f"{len(chunk):X}\r\n"
            client_socket.send(size_str.encode("utf-8"))
            client_socket.send(chunk)
            client_socket.send(b"\r\n")

    # 发送结束块
    client_socket.send(b"0\r\n\r\n")

def send_not_found(client_socket):
    global http_response
    http_response.set_response(404, "Not Found")
    # response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\nNot Found\r\n"
    response = http_response.gen_response()
    client_socket.send(response.encode("utf-8"))
def parse_range_header(range_header):
    """
    Parses the Range header and returns the start and end byte positions.
    Returns None if the Range header is invalid.
    """
    match = re.match(r'bytes=(\d*)-(\d*)', range_header)
    if not match:
        return None

    start, end = match.groups()
    start = int(start) if start else None
    end = int(end) if end else None
    return start, end

def is_valid_range(start, end, file_size):
    """
    Checks if the given byte range is valid for the file size.
    """
    if start is not None and start >= file_size:
        return False
    if end is not None and end <0:
        return False
    if start is not None and end is not None and start > end:
        return False
    return True

def split_and_convert(input_str):
    # 首先根据逗号分割成列表
    elements = input_str.split(',')
    result = []

    # 遍历每个分割后的元素，并根据减号分割，并将结果转换成tuple
    for element in elements:
        start, end = element.split('-')
        result.append((int(start), int(end)))

    return result

def send_file_with_range(client_socket, file_path, range_header):
    """
    Sends the requested part of the file based on the Range header.
    """
    global http_response
    file_size = os.path.getsize(file_path)
    ranges = split_and_convert(range_header)
    lenn = len(ranges)
    content_length = 0
    content = ""
    for i in range(lenn):
        
        start = ranges[i][0]
        end = ranges[i][1]

        if start is None and end is not None:
            # Case where range is -500 (last 500 bytes)
            start = max(file_size - end, 0)
            end = file_size - 1

        if not is_valid_range(start, end, file_size):
            http_response.set_response(416, "Range Not Satisfiable")
            response = http_response.gen_response()
            client_socket.send(response.encode("utf-8"))
            return

        if start is None or start < 0:
            start = 0
        if end is None or end >= file_size:
            end = file_size - 1

        content_length += end - start + 2#回车也算一个
        this_length = end - start + 1

        with open(file_path, "rb") as file:
            file.seek(start)
            # print(str(file.read(this_length)))
            content = content + str(file.read(this_length))[2:-1] + "\n"

    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    http_response.set_content_type(content_type)
    http_response.set_response(206, "Partial Content")
    http_response.add_header({'Content-Range': f'bytes {start}-{end}/{file_size}'})
    response_headers = http_response.gen_response_header(content_length)
    client_socket.send(response_headers.encode("utf-8") + content.encode("utf-8"))

# This is the modified version of the send_file function with support for Range headers
def modified_send_file(client_socket, file_path, headers):
    range_header = next((h for h in headers if h.startswith('Range: ')), None)
    if range_header:
        send_file_with_range(client_socket, file_path, range_header.split(": ", 1)[1])
    else:
        # Original send_file functionality
        send_file_chunked(client_socket, file_path)