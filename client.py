import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 5000))

# # test index page
# with open("./tests/test_requests/index_request.txt", "r") as f:
#     sock.send(f.read().encode("utf-8"))
# data = sock.recv(2048)
# print(data.decode("utf-8"))


# # test login page
# with open("./tests/test_requests/logger_name_request.txt", "r") as f:
#     sock.send(f.read().encode("utf-8"))
# data = sock.recv(2048)
# print(data.decode("utf-8"))


# test upload image
with open("./tests/test_requests/upload_image_request.txt", "r") as f:
    sock.send(f.read().encode("utf-8"))
    with open("./tests/test_media/LC-84.jpg", "rb") as image:
        image_data = image.read(2048)
        while image_data:
            sock.send(image_data)
            image_data = image.read(2048)

data = sock.recv(2048)
print(data.decode("utf-8"))
sock.close()
