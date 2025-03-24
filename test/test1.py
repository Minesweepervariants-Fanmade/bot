import socket
from pathlib import Path

SELF_PATH = Path(__file__).parent.__str__()


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.147.19.0', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip

if __name__ == '__main__':
    print(get_host_ip())
    print(SELF_PATH)