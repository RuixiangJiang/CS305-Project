import socket
import time

def parse_http_params(http_text):
    start_line, rest = http_text.split("\r\n", 1)
    method, path, _ = start_line.split(" ", 2)
    if "\r\n\r\n" in rest:
        headers, body = rest.split("\r\n\r\n", 1)
    else:
        headers, body = rest, ''
    headers = headers.split("\r\n")
    query_params = {}
    if '?' in path:
        path, query_string = path.split('?', 1)
        for param in query_string.split("&"):
            key_value = param.split("=")
            key = key_value[0]
            value = key_value[1] if len(key_value) > 1 else ''
            query_params[key] = value
    return method, path, query_params, headers, body

def simple_unquote(url):
    replacements = {
        '%20': ' ',
        '%2F': '/',
    }
    for encoded, decoded in replacements.items():
        url = url.replace(encoded, decoded)
    return url


class HttpResponse:
    def __init__(self):
        self.status_code = 200  # 默认状态码
        self.status_messages = {
            200: "OK",
            301: "Moved Permanently",
            302: "Found",
            400: "Bad Request",
            401: "Unauthorized",
            404: "Not Found",
            500: "Internal Server Error",
        }
        self.headers = {}
        self.content = ''
        self.content_type = 'text/html; charset=utf-8'  # 默认内容类型

    def set_response(self, status_code, content=''):
        self.status_code = status_code
        self.content = content

    def add_header(self, additional_headers):
        self.headers.update(additional_headers)

    def set_content_type(self, content_type):
        self.content_type = content_type

    def set_content(self, content):
        self.content = content

    def gen_response(self):
        # 确保内容类型被包含在头部中
        self.headers['Content-Type'] = self.content_type
        # 计算内容长度
        self.headers['Content-Length'] = str(len(self.content.encode('utf-8')))
        
        # 构造状态行和头部
        status_line = f"HTTP/1.1 {self.status_code} {self.status_messages.get(self.status_code, 'Unknown Status')}\r\n"
        header_lines = ''.join(f"{key}: {value}\r\n" for key, value in self.headers.items())
        response = f"{status_line}{header_lines}\r\n{self.content}"
        print("response status code: " + str(self.status_code))
        print("response header_lines:\n" + str(header_lines))
        return response
    def gen_response_header(self, content_length=0):
        # 确保内容类型被包含在头部中
        self.headers['Content-Type'] = self.content_type
        # 计算内容长度
        self.headers['Content-Length'] = str(content_length)
        
        # 构造状态行和头部
        status_line = f"HTTP/1.1 {self.status_code} {self.status_messages.get(self.status_code, 'Unknown Status')}\r\n"
        header_lines = ''.join(f"{key}: {value}\r\n" for key, value in self.headers.items())
        response = f"{status_line}{header_lines}\r\n"
        print("RESPONSE status code: " + str(self.status_code))
        print("RESPONSE header_lines:\n" + str(header_lines))
        return response

