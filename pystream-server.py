#!/usr/bin/env python

import argparse
import asyncio

from aiohttp import web


async def subscribe(request: web.Request) -> web.StreamResponse:
    stream = web.StreamResponse()
    await stream.prepare(request)
    request.app['streams'].append(stream)

    while request.transport is not None and not request.transport.is_closing():
        if request.app['heartbeat_timeout']:
            await asyncio.sleep(request.app['heartbeat_timeout'])
            await stream.write(request.app['heartbeat_message'])
        else:
            await asyncio.sleep(0.1)

    await stream.write_eof()
    request.app['streams'].remove(stream)

    return stream


async def write_to_stream(request: web.Request) -> web.Response:
    data = await request.read()

    for stream in request.app['streams']:
        if not data:
            await stream.write_eof()
            continue

        await stream.write(data + b'\r\n')

    return web.Response()


async def on_shutdown(app: web.Application) -> None:
    for stream in app['streams']:
        if stream.task is not None and not stream.task.done():
            await stream.write_eof()


async def cleaner(app: web.Application) -> None:
    try:
        while True:
            for stream in app['streams'[:]]:
                if stream.task is None or stream.task.done():
                    app['streams'].remove(stream)

            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass


async def start_cleaner(app: web.Application) -> None:
    app['cleaner'] = asyncio.create_task(cleaner(app))


async def stop_cleaner(app: web.Application) -> None:
    app['cleaner'].cancel()
    await app['cleaner']


def main() -> None:
    parser = argparse.ArgumentParser(prog=__name__, description='Simple python stream server')
    parser.add_argument('-a', '--address', type=str, default='0.0.0.0', help='binding address')
    parser.add_argument('-p', '--port', type=int, default=8080, help='binding port')
    parser.add_argument('-m', '--heartbeat-message', type=str, default=0, help='heartbeat message')
    parser.add_argument(
        '-t', '--heartbeat-timeout', type=float, default=0, help='heartbeat timeout'
    )
    args = parser.parse_args()

    app = web.Application()
    app['streams'] = []
    app['heartbeat_timeout'] = args.heartbeat_timeout
    app['heartbeat_message'] = f'{args.heartbeat_message}\r\n'.encode('utf-8')

    app.router.add_get('/', subscribe)
    app.router.add_put('/', write_to_stream)

    app.on_startup.append(start_cleaner)
    app.on_shutdown.append(on_shutdown)
    app.on_shutdown.append(stop_cleaner)

    web.run_app(app, host=args.address, port=args.port)


if __name__ == '__main__':
    main()
