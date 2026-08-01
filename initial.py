
from websockets import SecurityError

filename = "something.pdf"


def check_method(filename):
    if not filename.endswith(".pdf"):
        raise SecurityError("File is not a pdf")
    return True


print(check_method(filename))