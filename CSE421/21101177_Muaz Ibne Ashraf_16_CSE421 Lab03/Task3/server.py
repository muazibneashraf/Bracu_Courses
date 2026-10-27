import socket
import threading

fmt = "utf-8"
buffer_size = 16
conn_close = "end"
port_no = 8080
host_name = socket.gethostname()
host_ip_addr = socket.gethostbyname(host_name)

server_socket_addr = (host_ip_addr, port_no)
server = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
server.bind(server_socket_addr)

server.listen()
print("\nThe server is listening at port 8080")

def manage_clients(conn, ip):
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
                v = "AEIOUaeiou"
                c = 0
                for i in msg:
                    if i in v:
                        c += 1

                if c == 0:
                    conn.send("Not enough vowels".encode(fmt))
                elif c <= 2:
                    conn.send("Enough vowels I guess".encode(fmt))
                else:
                    conn.send("Too many vowels".encode(fmt))

    conn.close()

while True:
    conn, ip = server.accept()
    thread = threading.Thread(target = manage_clients, args = (conn, ip))
    thread.start()