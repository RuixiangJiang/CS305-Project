import socket
import threading
from Handle import handle_request
from http_util import parse_http_params



# def main():
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     server_socket.bind(("localhost", 8080))
#     # server_socket.bind(("0.0.0.0", 8080))
#     server_socket.listen(5)
#     print("Server listening on port 8080...")

#     while True:
#         client_socket, client_address = server_socket.accept()
#         print(f"Accepted connection from {client_address}")
#         handle_request(client_socket)
#         client_socket.close()
        
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8080))
    server_socket.listen(5)
    print("Server listening on port 8080...")

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
                request_data = client_socket.recv(1024).decode("utf-8")
                method, path, query_params, headers, body = parse_http_params(request_data)
                headers_dict = dict(line.split(": ", 1) for line in headers)
                connection = headers_dict.get('Connection', 'Close')
                print("connection: ", connection)
                handle_request(client_socket, request_data)
                if connection.lower() == 'close':
                    break
            except socket.timeout:
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
