import asyncio


async def tcp_echo_client(loop):
    stream_in, stream_out = await asyncio.open_connection(
        '10.0.1.3', 102, loop=loop)

    data = await stream_in.read(100)
    print(f'Received: {data.decode()}')

    message = 'charging'
    print(f'Send: {message}')
    stream_out.write(message.encode())

    data = await stream_in.read(100)
    print(f'Received: {data.decode()}')

    message = 'success'
    print(f'Send: {message}')
    stream_out.write(message.encode())

    await asyncio.sleep(10)

    # print('Closing the socket')
    # stream_out.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(tcp_echo_client(loop))
loop.close()
