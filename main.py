import socket
import threading
from Handle import handle_request



def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8080))
    # server_socket.bind(("0.0.0.0", 8080))
    server_socket.listen(5)
    print("Server listening on port 8080...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Accepted connection from {client_address}")
        handle_request(client_socket)
        client_socket.close()
        
''' 
失败尝试Persistent Connection & Many Clients, 文件稍大传一半时socket会断开
不过好像不用那么复杂就能过测试脚本

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8000))
    server_socket.listen(5)
    print("Server listening on port 8000...")

    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=client_thread, args=(client_socket, client_address))
        thread.start()

def client_thread(client_socket, client_address):
    print(f"Handling connection from {client_address}")
    keep_handle_request(client_socket)
    print(f"Connection with {client_address} closed")
    
def keep_handle_request(client_socket, timeout=30):
    client_socket.settimeout(timeout)
    try:
        while True:
            try:
                handle_request(client_socket)
            except socket.timeout:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
'''
if __name__ == "__main__":
    main()
