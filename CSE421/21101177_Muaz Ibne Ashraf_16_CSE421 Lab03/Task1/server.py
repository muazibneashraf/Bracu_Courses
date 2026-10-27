import socket

fmt = "utf-8"
buffer_size = 16
conn_close = "end"
port_no = 8080
host_name = socket.gethostname()
host_ip_addr = socket.gethostbyname(host_name)

server_socket_addr = (host_ip_addr, port_no)
server = socket.socket(socket.AF_INET ,  socket.SOCK_STREAM)
server.bind(server_socket_addr)

server.listen()
print("\nThe server is listening at port 8080")

while True:
    conn, ip = server.accept()
    print(f"Connected to {ip}")
    connected = True
    while connected:
        message_len = conn.recv(buffer_size).decode(fmt)
        print("Message length is", message_len)
        if message_len:
            msg_length = int(message_len)
            msg = conn.recv(msg_length).decode(fmt)

            if msg == conn_close:
                conn.send("Connection closed\n".encode(fmt))
                print(f"Connection terminated with {ip} \n")
                connected = False
            else:
                print(msg)
                conn.send("\nMessage received.".encode(fmt))

    conn.close()