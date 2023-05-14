import sys

import uvicorn
from fastapi import FastAPI
from starlette.websockets import WebSocket
from queue import Queue
from ds18b20 import DS18B20
import schedule
import logging

app = FastAPI()
data_queue = Queue()


@app.get("/sensor")
def sensorData():
    with open("temps.log") as file:
        return file.read()


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    while True:
        if not data_queue.empty():
            await ws.send_text(data_queue.get())


def getTemps(logger):
    sensors = DS18B20.get_all_sensors()
    for sensor in sensors:
        data = f"temp+{sensor.get_id()}:{sensor.get_temperature()}"
        data_queue.put(data)
        logger.info(data)


def getLogger(filename: str):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    return logger


if __name__ == '__main__':
    schedule.every(15).minutes.do(getTemps(getLogger("temps.log")))

    uvicorn.run(app, host="0.0.0.0", port=2002)
