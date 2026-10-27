import socket

fmt = "utf-8"
buffer_size = 16
conn_close = "end"
port_no = 8080
host_name = socket.gethostname()
host_ip_addr = socket.gethostbyname(host_name)

server_socket_addr = (host_ip_addr, port_no)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(server_socket_addr)

def send_message(msg):
    message = msg.encode(fmt)
    msg_len = str(len(message)).encode(fmt)
    msg_len += b" " * (buffer_size - len(msg_len))

    client.send(msg_len)
    client.send(message)

    print(client.recv(2048).decode(fmt))

while True:
    inp = input("Enter hours: ")
    if inp == "end":
        send_message(conn_close)
        break
    else:
        send_message(inp)
