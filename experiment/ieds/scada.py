from asyncio import get_event_loop, start_server


async def handle_echo(stream_in, stream_out):
    addr = stream_out.get_extra_info('peername')

    data = 'read->ChargingLD/DRCT.Comm.func'
    print(f"Send: {data}")
    stream_out.write(data.encode())
    await stream_out.drain()

    data = await stream_in.read(100)
    message = data.decode()
    print(f"Received: {message} {addr}")

    data = 'write->BatteryLD/ZBTC.BatChaSt.setVal->2'  # charge
    print(f"Send: {data}")
    stream_out.write(data.encode())
    await stream_out.drain()

    data = await stream_in.read(100)
    message = data.decode()
    print(f"Received {message} from {addr}")

    # print("Close the client socket\n")
    # stream_out.close()

loop = get_event_loop()
coroutine = start_server(handle_echo, '10.0.1.3', 102, loop=loop)
server = loop.run_until_complete(coroutine)

print('Serving on {}'.format(server.sockets[0].getsockname()))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
