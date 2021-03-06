from asyncio import get_event_loop, start_server
from struct import pack
from datetime import datetime


# https://tools.ietf.org/html/rfc1006
async def handle_echo(stream_in, stream_out):
    addr = stream_out.get_extra_info('peername')

    data = pack('22B', 0x03, 0x00, 0x00, 0x16, 0x11, 0xe0, 0x00, 0x00, 0x00,
                0x01, 0x00, 0xc0, 0x01, 0x0d, 0xc2, 0x02, 0x00, 0x01, 0xc1,
                0x02, 0x00, 0x01)
    stream_out.write(data)
    await stream_out.drain()
    print(f'{datetime.now()} {addr} Sent: COTP')

    data = await stream_in.read(1024)
    print(f'{datetime.now()} {addr} Recv: COTP')

    data = pack('187B', 0x03, 0x00, 0x00, 0xbb, 0x02, 0xf0, 0x80, 0x0d, 0xb2,
                0x05, 0x06, 0x13, 0x01, 0x00, 0x16, 0x01, 0x02, 0x14, 0x02,
                0x00, 0x02, 0x33, 0x02, 0x00, 0x01, 0x34, 0x02, 0x00, 0x01,
                0xc1, 0x9c, 0x31, 0x81, 0x99, 0xa0, 0x03, 0x80, 0x01, 0x01,
                0xa2, 0x81, 0x91, 0x81, 0x04, 0x00, 0x00, 0x00, 0x01, 0x82,
                0x04, 0x00, 0x00, 0x00, 0x01, 0xa4, 0x23, 0x30, 0x0f, 0x02,
                0x01, 0x01, 0x06, 0x04, 0x52, 0x01, 0x00, 0x01, 0x30, 0x04,
                0x06, 0x02, 0x51, 0x01, 0x30, 0x10, 0x02, 0x01, 0x03, 0x06,
                0x05, 0x28, 0xca, 0x22, 0x02, 0x01, 0x30, 0x04, 0x06, 0x02,
                0x51, 0x01, 0x61, 0x5e, 0x30, 0x5c, 0x02, 0x01, 0x01, 0xa0,
                0x57, 0x60, 0x55, 0xa1, 0x07, 0x06, 0x05, 0x28, 0xca, 0x22,
                0x02, 0x03, 0xa2, 0x07, 0x06, 0x05, 0x29, 0x01, 0x87, 0x67,
                0x01, 0xa3, 0x03, 0x02, 0x01, 0x0c, 0xa6, 0x06, 0x06, 0x04,
                0x29, 0x01, 0x87, 0x67, 0xa7, 0x03, 0x02, 0x01, 0x0c, 0xbe,
                0x2f, 0x28, 0x2d, 0x02, 0x01, 0x03, 0xa0, 0x28, 0xa8, 0x26,
                0x80, 0x03, 0x00, 0xfd, 0xe8, 0x81, 0x01, 0x05, 0x82, 0x01,
                0x05, 0x83, 0x01, 0x0a, 0xa4, 0x16, 0x80, 0x01, 0x01, 0x81,
                0x03, 0x05, 0xf1, 0x00, 0x82, 0x0c, 0x03, 0x0C, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10)
    stream_out.write(data)
    await stream_out.drain()
    print(f'{datetime.now()} {addr} Sent: MMS-Initiate')

    data = await stream_in.read(1024)
    print(f'{datetime.now()} {addr} Recv: MMS-Initiate')

    data = pack('72B', 0x03, 0x00, 0x00, 0x48, 0x02, 0xf0, 0x80, 0x01, 0x00,
                0x01, 0x00, 0x61, 0x3b, 0x30, 0x39, 0x02, 0x01, 0x03, 0xa0,
                0x34, 0xa0, 0x32, 0x02, 0x01, 0x01, 0xa4, 0x2d, 0xa1, 0x2b,
                0xa0, 0x29, 0x30, 0x27, 0xa0, 0x25, 0xa1, 0x23, 0x1a, 0x0a,
                0x43, 0x68, 0x61, 0x72, 0x67, 0x69, 0x6e, 0x67, 0x4c, 0x44,
                0x1a, 0x15, 0x44, 0x52, 0x43, 0x54, 0x24, 0x53, 0x54, 0x24,
                0x43, 0x6f, 0x6d, 0x6d, 0x24, 0x66, 0x75, 0x6e, 0x63, 0x74,
                0x69, 0x6f, 0x6e)
    stream_out.write(data)
    await stream_out.drain()
    print(
        f'{datetime.now()} {addr} '
        'Sent: MMS-Read >>> ChargingLD/DRCT.Comm.function')

    data = await stream_in.read(1024)
    print(f'{datetime.now()} {addr} Recv: MMS-Read >>> Recharge')

    data = pack('76B', 0x03, 0x00, 0x00, 0x4C,  # quantos bytes esse pack
                0x02, 0xf0, 0x80, 0x01, 0x00, 0x01, 0x00,
                0x61, 0x3F,  # quantos bytes a baixo
                0x30, 0x3D,  # quantos bytes a baixo
                0x02, 0x01, 0x03, 0xa0, 0x38,  # quantos bytes a baixo

                0xa0, 0x36,  # quantos bytes a baixo
                0x02, 0x01, 0x02,
                0xa5, 0x31,  # quantos bytes a baixo
                0xa0, 0x2A,  # quantos bytes nos 5 proximos blocos
                0x30, 0x28,  # quantos bytes nos 4 proximos blocos
                0xa0, 0x26,  # quantos bytes nos 3 proximos blocos
                0xa1, 0x24,  # quantos bytes nos 2 proximos blocos

                0x1a, 0x09,  # quantos bytes nesse bloco
                0x42, 0x61, 0x74, 0x74, 0x65, 0x72, 0x79, 0x4c, 0x44,

                0x1a, 0x17,  # quantos bytes nesse bloco
                0x5a, 0x42, 0x54, 0x43,
                0x24, 0x53, 0x50, 0x24, 0x42, 0x61, 0x74, 0x43, 0x68, 0x61,
                0x53, 0x74, 0x24, 0x73, 0x65, 0x74, 0x56, 0x61, 0x6c,

                0xa0, 0x03, 0x85, 0x01, 0x02)
    stream_out.write(data)
    await stream_out.drain()
    print(
        f'{datetime.now()} {addr} '
        'Sent: MMS-Write >>> BatteryLD/ZBTC.BatChaSt.setVal->2')

    data = await stream_in.read(1024)
    print(f'{datetime.now()} {addr} Recv: MMS-Write >>> Success')

    print("Closing the client socket\n")
    stream_out.close()

loop = get_event_loop()
coroutine = start_server(handle_echo, '10.0.1.3', 102, loop=loop)
server = loop.run_until_complete(coroutine)

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
