from socket import*
import struct
import json
import os
import sys
import time

# 用户的文件夹路径
FILEPATH = "fileClient/"

# 创建客户端
client = socket(AF_INET, SOCK_STREAM)
ip_port = ('127.0.0.1', 21565)
buffSize = 1024
client.connect(ip_port)
print("connecting...")

# 开始通信
while True:
    # 用户选择要进行的服务，将选择发送给服务器
    select = input("请输入要选择的服务： 1--上传文件   2--下载文件  0--退出系统\n")
    client.send(bytes(select, "utf-8"))

    # 上传文件
    if select == "1":
        fileName = input("请输入要上传的文件名加后缀：").strip()
        fileInfor = FILEPATH + fileName

        # 得到文件的大小
        filesize_bytes = os.path.getsize(fileInfor)

        # 创建复制文件
        fileName = "" + fileName

        # 创建字典用于报头
        dirc = {"fileName": fileName,
                "fileSize": filesize_bytes}

        # 将字典转为JSON字符，再将字符串的长度打包
        head_infor = json.dumps(dirc)
        head_infor_len = struct.pack('i', len(head_infor))

        # 先发送报头长度，然后发送报头内容
        client.send(head_infor_len)
        client.send(head_infor.encode("utf-8"))

        # 发送真实文件
        with open(fileInfor, 'rb') as f:
            data = f.read()
            client.sendall(data)
            f.close()

        # 服务器若接受完文件会发送信号，客户端接收
        completed = client.recv(buffSize).decode("utf-8")
        if completed == "1":
            print("上传成功")
    # 下载文件
    elif select == "2":
        # 用户输入文件信息，发送给服务器
        fileName = input("请输入要下载的文件名加后缀：").strip()
        client.send(bytes(fileName, "utf-8"))

        # 默认文件存在，接受并解析报头的长度，接受报头的内容
        head_struct = client.recv(4)
        head_len = struct.unpack('i', head_struct)[0]
        data = client.recv(head_len)

        # 解析报头字典
        head_dir = json.loads(data.decode('utf-8'))
        filesize_b = head_dir["fileSize"]
        filename = head_dir["fileName"]

        # 接受真实的文件内容
        recv_len = 0
        recv_mesg = b''

        f = open("%s%s" % (FILEPATH, filename), "wb")

        while recv_len < filesize_b:
            if filesize_b - recv_len > buffSize:
                # 假设未上传的文件数据大于最大传输数据
                recv_mesg = client.recv(buffSize)
                f.write(recv_mesg)
                recv_len += len(recv_mesg)
            else:
                # 需要传输的文件数据小于最大传输数据大小
                recv_mesg = client.recv(filesize_b - recv_len)
                recv_len += len(recv_mesg)
                f.write(recv_mesg)
                f.close()
                print("文件接收完毕！")

        # 向服务器发送信号，文件已经上传完毕
        completed = "1"
        client.send(bytes(completed, "utf-8"))
    #退出客户端
    else:
        print("退出系统！")
        client.close()
        break

