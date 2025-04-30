#!/usr/bin/env python3
import socket
import sys
import ipaddress
import struct
import threading
import time

from packformat import SIGN, NEW_CONN, CONN_TO, FIN_CONN
from window import ChatWindow


if len(sys.argv)!=6:
    print('Ожидается 5 параметров: имя ip_клиента port_клиента ip_сервера port_сервера')
    exit()

try:
    if not ipaddress.ip_address(sys.argv[2]):
        print('Неправильный ip-адрес клиента')
        exit()
    if not ipaddress.ip_address(sys.argv[4]):
        print('Неправильный ip-адрес сервера')
        exit()
except ValueError:
    print('Неправильный ip-адрес')
    exit()

name = sys.argv[1]
ip = sys.argv[2]
serv_ip = sys.argv[4]

try:
    port = int(sys.argv[3])
    serv_port = int(sys.argv[5])
except ValueError:
    print('Неверный порт')
    exit()

win = ChatWindow()

is_running = True
is_connected = False

sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_udp.settimeout(0.1)
sock_tcp.settimeout(0.1)

tcp_lock = threading.Lock()

try:
    sock_tcp.bind((ip, port))
    sock_udp.bind((ip, port))
except OSError as e:
    if e.errno == 98:
        print('Порт занят')
    else:
        print(e)
    exit()

output_lock = threading.Lock()

def connect():
    global is_connected, is_running
    message = SIGN + struct.pack('!bb', NEW_CONN, len(name)) + name.encode()
    sock_udp.sendto(message, (serv_ip, serv_port))

    win.output('', title='Установка соединения', time=False)

    try:
        sock_tcp.connect((serv_ip, serv_port))
    except ConnectionRefusedError:
        win.clear_output()
        win.output('Сервер недоступен. Нажмите любую клавишу для выхода...')

        is_connected = True
        is_running = False
        win.window.bind('<Key>', on_close)
        return
    is_connected = True

    win.clear_output()
    win.show_input()

def get_conn_mess():
    while not is_connected:
        pass
    while is_running:
        try:
            pack, addr = sock_udp.recvfrom(1024)
        except TimeoutError:
            continue
        except Exception as e:
            with output_lock:
                win.output(f'{str(e)}')
                break
        if pack[:5]!=SIGN:
            continue
        mess_type = pack[5]
        name_len = pack[6]
        new_name = pack[7:7+name_len].decode()
        new_ip = socket.inet_ntoa(pack[7+name_len:])
        with output_lock:
            win.output(f'Пользователь {new_name}({new_ip}) {"подключён" if mess_type == NEW_CONN else "отключён"}.')

def send_message():
    win.error('')
    mess = win.input()
    if not mess.find('\\') == -1:
        win.error('Недопустимый символ "\\"')
        return
    mess = mess.encode()
    mess = SIGN + struct.pack('!b', len(mess)) + mess
    with tcp_lock:
        sock_tcp.send(mess)
    win.clear_input()

def get_message():
    global is_running
    while not is_connected:
        pass
    with sock_tcp:
        while is_running:
            try:
                with tcp_lock:
                    pack = sock_tcp.recv(1024)
            except TimeoutError:
                time.sleep(0.01)
                continue
            if not pack:
                win.output(string = 'Сервер недоступен. Нажмите любую клавишу для выхода...')
                win.hide_input()
                is_running = False
                win.window.bind('<Key>', on_close)
            if pack[:5]!=SIGN:
                continue
            mess_len = pack[5]
            mess = pack[6:6+mess_len].decode()
            name_len = pack[6+mess_len]
            src_name = pack[7+mess_len:7+name_len+mess_len].decode()
            src_ip = socket.inet_ntoa(pack[7+name_len+mess_len:])
            with output_lock:
                win.output(f'{src_name}({src_ip}): {mess}')

def on_close(event = None):
    global is_running
    is_running = False
    conn_thr.join()
    rec_udp_thr.join()
    rec_tcp_thr.join()
    sock_tcp.close()
    sock_udp.close()
    win.window.destroy()

try:
    conn_thr = threading.Thread(target = connect)
    rec_udp_thr = threading.Thread(target = get_conn_mess)
    rec_tcp_thr = threading.Thread(target= get_message)
    conn_thr.start()
    rec_udp_thr.start()
    rec_tcp_thr.start()
    win.window.protocol('WM_DELETE_WINDOW', on_close)
    win.btn.config(command=send_message)
    win.window.mainloop()
except KeyboardInterrupt:
    is_running = False
    conn_thr.join()
    rec_udp_thr.join()
    rec_tcp_thr.join()
finally:
    sock_tcp.close()
    sock_udp.close()



