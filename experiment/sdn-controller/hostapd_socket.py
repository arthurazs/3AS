from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from socket import error as socket_error
from select import select
from json import loads


class HostapdSocket:
    LOCAL_IP = '10.0.0.1'
    def __init__(
            self, logger, address=LOCAL_IP, port=10000, portDict={}):

        # Create a TCP/IP socket
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        # Bind the socket to the port
        self.server_address = (address, port)
        self.logger = logger
        self.logger.info('>>> hostapd_socket: Starting up on {}:{}'.format(
            address, port))
        self.sock.bind(self.server_address)

        # Listen for incoming connections
        self.sock.listen(10)

        self.portDict = portDict

        self.inputs = [self.sock]
        self.address = {}

        self.running = True

    def stop_socket(self):
        self.running = False
        self.logger.info(">>> hostapd_socket: Stopping")

    def start_socket(self):
        self.logger.info('>>> hostapd_socket: Running')
        while self.running:

            readable, writable, exceptional = select(self.inputs, [], [])
            for client in readable:
                if client is self.sock:
                    # Wait for a connection
                    connection, client_address = client.accept()
                    connection.setblocking(False)
                    self.inputs.append(connection)
                    self.address[connection] = client_address
                else:
                    try:
                        # Receive the data in small chunks and retransmit it
                        data = client.recv(1024)
                        if not self.handle_data(data, client):
                            raise socket_error
                        client.close()
                        if client in self.inputs:
                            self.inputs.remove(client)
                        if client in self.address:
                            del self.address[client]
                    except socket_error:
                        # Clean up the connection
                        client.close()
                        if client in self.inputs:
                            self.inputs.remove(client)
                        if client in self.address:
                            del self.address[client]

    def handle_data(self, data, connection):
        if data:
            if data.strip().lower() == "quit":
                self.logger.info(
                    '>>> hostapd_socket: {} exiting...'.format(connection))
                return False
            else:
                self.logger.info(
                    ">>> hostapd_socket: New data from {}:{} > {}"
                    .format(
                        self.address[connection][0],
                        self.address[connection][1],
                        data))

                # self.logger.info('>>> hostapd_socket: Sending data back...')
                connection.sendall(data)
                info = loads(data)

                if 'AUTH-OK' in info:
                    address = info['AUTH-OK']['address']
                    self.portDict[address] = info['AUTH-OK']
                elif 'AUTH-NOT' in info:
                    address = info['AUTH-NOT']['address']
                    if address in self.portDict:
                        del self.portDict[address]

                self.logger.info(
                    '>>> hostapd_socket: Authorized Addresses {}'
                    .format(self.portDict.keys()))
                return True
        else:
            return False


class Logger:
    def __init__(self):
        pass

    def info(self, msg):
        print(msg)


if __name__ == "__main__":
    hostapd_socket = HostapdSocket(Logger())
    hostapd_socket.start_socket()
