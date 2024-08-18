import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))
sock.sendall(bytes('Hello, world', encoding='UTF-8'))
data = sock.recv(1024)
sock.close()
print(data)
