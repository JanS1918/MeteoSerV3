import asyncio
from hbmqtt.broker import Broker

config = {
    "listeners": {"default": {"type": "tcp", "bind": "127.0.0.1:1883"}},
    "sys_interval": 10,
    "auth": {"allow-anonymous": True},
}

broker = Broker(config)


async def start_broker():
    await broker.start()
    # esperar indefinidamente
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(start_broker())
