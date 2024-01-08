import os
from http_util import parse_http_params, simple_unquote, HttpResponse


def parse_query_params(request_data):
    # Extract query string from request_data
    _, _, query_string = request_data.partition("\r\n\r\n")

    # Parse query parameters
    query_params = {}
    for param in query_string.split("&"):
        key_value = param.split("=")
        key = key_value[0]
        value = key_value[1] if len(key_value) > 1 else ''
        query_params[key] = value

    return query_params


def percent_encode_url(url):
    return url


def send_directory_listing(client_socket, dir_path, request, http_response: HttpResponse):
    _, _, query_params, _, _ = parse_http_params(request)
    file_list = os.listdir(dir_path)
    # SUSTech-HTTP=1
    if query_params.get('SUSTech-HTTP', '0') == '1':
        return_list = []
        for file in file_list:
            file_path = os.path.join(dir_path, file)
            if os.path.isdir(file_path):
                file += "/"
                return_list.append(file)
            else:
                return_list.append(file)
        return_list.sort()
        http_response.set_response(200, str(return_list))
        response = http_response.gen_response()
        client_socket.send(response.encode())
        return
    # if not request:
    #     query_params = parse_query_params(request)
    #     sustech_http = int(query_params.get('SUSTech-HTTP', '0'))
    #     print("sustech-http =", sustech_http)
    
    content = f"""
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        </head>
        <body>
            <script src="/web/script.js"></script>
            <h1>File Listing</h1>
            <input type="file" id="fileInput">
            <button onclick="uploadFile('{percent_encode_url(dir_path)}')">Upload</button>
            <ul>
    """
    content += f'<li><a href="{percent_encode_url("..")}">返回上一级</a></li>'
    content += f'<li><a href="{percent_encode_url("/")}">返回根目录</a></li>'

    for file in file_list:
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            file += "/"
            content += f'''
                <li>
                    <a href="{percent_encode_url(file)}">{file}</a> 
                    <button onclick="deleteFile('{percent_encode_url(file_path)}')">Delete</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 0)">Download (SUSTech-HTTP=0)</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 1)">Download (SUSTech-HTTP=1)</button>
                </li>
            '''
        else:
            content += f'''
                <li>
                    <a href="{percent_encode_url(file)}">{file}</a> 
                    <button onclick="deleteFile('{percent_encode_url(file_path)}')">Delete</button>
                    <button onclick="downloadFile('{percent_encode_url(file)}', 0)">Download</button>
                </li>
            '''

    content += """
            </ul>
        </body>
        </html>
    """

    # content_encoded = content.encode("utf-8")
    # response_headers = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(content_encoded)}\r\n\r\n"
    # client_socket.send(response_headers.encode('utf-8') + content_encoded)
    http_response.set_response(200, content)
    response = http_response.gen_response()
    client_socket.send(response.encode())
