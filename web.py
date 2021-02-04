# -*- coding: utf-8 -*-
# @Time    : 2021/1/24 18:43
# @Author  : RYW
# @Software: PyCharm

import socket


def main():
    # 1、创建套接字
    servier_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 2、绑定本地（ip，端口）
    servier_socket.bind(("", 3000))
    # 3、监听
    servier_socket.listen(128)
    # 4、等待客户端请求
    while True:
        new_client_socket, client_addr = servier_socket.accept()
        recv_data = new_client_socket.recv(1024).decode('utf8')
        print("客户端的请求内容为：%s" % recv_data)
        # 给客户端回送一个固定页面的内容
        if recv_data:
            response = "HTTP/1.1 200 ok\r\n" + "\r\n" + "<h1>hello word</h1>"
            new_client_socket.send(response.encode('utf8'))
        else:
            break
        new_client_socket.close()
        print("这个客户机服务关闭，已关闭")
    servier_socket.close()


if __name__ == "__main__":
    main()