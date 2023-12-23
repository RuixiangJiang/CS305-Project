import base64
import socket
import json


def add_credentials(username, password):
    with open('users.json', 'r+') as user_file:
        users = json.load(user_file)
        users[username] = password
        user_file.seek(0)  # 移动到文件开头
        json.dump(users, user_file, indent=4)
        user_file.truncate()  # 删除文件中剩余的任何数据
        
def check_credentials(username, password):
    with open('users.json', 'r') as user_file:
        users = json.load(user_file)
        return users.get(username) == password

def check_request_auth(request):
    headers = request.split('\r\n')
    auth_header = [h for h in headers if h.startswith('Authorization: Basic')]
    if auth_header:
        # 提取并解码凭证
        _, _, encoded_credentials = auth_header[0].split(' ', 2)
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        username, password = decoded_credentials.split(':', 1)
        print("username = " + str(username))
        print("password = " + str(password))
        if check_credentials(username, password):
            # 凭证有效
            print("valid aouthorization")
            return username
        else:
            # 凭证无效
            return False
    else:
        # 没有凭证
        return False
def add_request_auth(request): 
    headers = request.split('\r\n')
    auth_header = [h for h in headers if h.startswith('Authorization: Basic')]
    if auth_header:
        # 提取并解码凭证
        _, _, encoded_credentials = auth_header[0].split(' ', 2)
        decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        new_username, new_password = decoded_credentials.split(':', 1)
        add_credentials(new_username, new_password)
        print(f"New user registered: {new_username}")
        return new_username
    else:
        # 没有凭证
        return False
    
    
# decoded_credentials = base64.b64decode("Y2xpZW50MToxMjM=").decode('utf-8')
# username, password = decoded_credentials.split(':', 1)
# add_credentials(username, password)