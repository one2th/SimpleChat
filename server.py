import datetime
import socket
import struct
import sys
import ipaddress
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor

from packformat import SIGN, NEW_CONN, CONN_TO, FIN_CONN

is_running = True

def main():
    if len(sys.argv)!=3:
        print('Ожидается два параметра: ip port')
        exit()

    try:
        if not ipaddress.ip_address(sys.argv[1]):
            print('Неправильный ip-адрес')
            exit()
    except ValueError:
        print('Неправильный ip-адрес')
    ip = sys.argv[1]

    try:
        port = int(sys.argv[2])
    except ValueError:
        print('Неверный порт')
        exit()

    class User:
        name: str
        ip: str
        port: int
        sock: socket.socket
        sock_lock: threading.Lock

        def __init__(self, name: str, addr :tuple, sock: socket.socket):
            self.name = name
            self.ip = addr[0]
            self.port = addr[1]
            self.sock = sock
            self.sock_lock = threading.Lock()

    users = []

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    output_lock = threading.Lock()
    us_list_lock = threading.Lock()
    udp_lock = threading.Lock()


    def connect():
        global is_running
        with  udp_sock, tcp_sock, ThreadPoolExecutor(max_workers=20) as executor:
            try:
                udp_sock.bind((ip, port))
                tcp_sock.bind((ip, port))
            except OSError as e:
                if e.errno == 98:
                    print('Порт занят')
                else:
                    print(e)
                exit()
            tcp_sock.listen(5)
            tcp_sock.settimeout(5)

            futures = []

            while is_running:
                try:
                    pack, addr = udp_sock.recvfrom(1024)
                    if pack[:5]!=SIGN:
                        continue
                    us_ip = addr[0]
                    us_port = addr[1]
                    us_name = pack[7:].decode()
                    with output_lock:
                        print(f'[INFO] [{datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}]\n'
                              f'Пользователь {us_name}({us_ip}) запрашивает подключение.')

                    try:
                        cl_socket, cl_addr = tcp_sock.accept()
                        with output_lock:
                            print(f'[INFO] [{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}]\n'
                                  f'Пользователь {us_name}({us_ip}) подключен.')
                    except TimeoutError:
                        to_mess = SIGN + struct.pack('!b', CONN_TO)
                        udp_sock.sendto(to_mess, (us_ip, us_port))
                        continue

                    user = User(us_name, (us_ip, us_port), cl_socket)
                    new_conn_mess = pack + socket.inet_aton(us_ip)
                    for usr in users:
                        udp_sock.sendto(new_conn_mess, (usr.ip, usr.port))
                    users.append(user)

                    future = executor.submit(get_message, user)
                    futures.append(future)
                except KeyboardInterrupt as e:
                    is_running = False

            for future in futures:
                future.cancel()

    def get_message(user: User):
        with user.sock:
            user.sock.settimeout(0.05)
            while is_running:
                try:
                    with user.sock_lock:
                        message = user.sock.recv(1024)
                except TimeoutError:
                    time.sleep(0.001)
                    continue
                if not message:
                    with output_lock:
                        print(f'[INFO] [{datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}]\n'
                              f'Пользователь {user.name}({user.ip}) отключён.')
                    packet = SIGN + struct.pack('!bb', FIN_CONN, len(user.name)) + user.name.encode() + \
                             socket.inet_aton(user.ip)
                    with us_list_lock:
                        users.remove(user)
                        users_copy = users.copy()
                    with udp_lock:
                        for usr in users_copy:
                            udp_sock.sendto(packet, (usr.ip, usr.port))
                    break
                if message[:5]!=SIGN:
                    continue
                message = message + struct.pack('!b', len(user.name)) + user.name.encode() + \
                          socket.inet_aton(user.ip)
                with us_list_lock:
                    for usr in users:
                        with usr.sock_lock:
                            usr.sock.send(message)

    try:
        connect()
    finally:
        global is_running
        is_running = False

if __name__ == '__main__':
    main()