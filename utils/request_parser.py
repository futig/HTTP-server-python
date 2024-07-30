from models.user_info import UserInfo


def parse_request(request: str):
    request_dict = dict()
    split_request = request.split("\n")
    first_line = split_request.pop(0)
    (request_dict["method"], request_dict["url"],
     request_dict["http_version"]) = first_line.split()

    request_body = split_request.pop(-1)  # for Post
    user_agent = [line.split(": ") for line in split_request
                  if "User-Agent" in line][0]
    request_dict[user_agent[0]] = user_agent[1]
    return request_dict, request_body


def parse_request_body(body: str):  # name=Vasia&surname=Petrovich&submit=Send
    if not body:
        return
    replaced = body.replace('+', ' ')
    info_dict = dict(pair.split("=") for pair in replaced.split('&') if pair)
    return UserInfo(info_dict["name"], info_dict["surname"])
