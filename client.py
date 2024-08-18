import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))

# # test index page
# with open("./tests/test_requests/index_request.txt", "r") as f:
#     sock.sendall(f.read().encode("utf-8"))
# data = sock.recv(2048)
# print(data.decode("utf-8"))


# # test login page
# with open("./tests/test_requests/logger_name_request.txt", "r") as f:
#     sock.sendall(f.read().encode("utf-8"))
# data = sock.recv(2048)
# print(data.decode("utf-8"))


# test upload image
with open("./tests/test_requests/upload_image_request.txt", "r") as f:
    with open("./tests/test_media/LC-84.jpg", "rb") as image:
        sock.sendall(f.read().encode("utf-8") + image.read())
data = sock.recv(2048)
print(data.decode("utf-8"))
sock.close()
