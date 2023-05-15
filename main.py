import uvicorn
from fastapi import FastAPI
from fastapi_amis_admin.admin import AdminSite, Settings
from fastapi_scheduler import SchedulerAdmin
from starlette.websockets import WebSocket
from starlette.responses import PlainTextResponse
from queue import Queue
from ds18b20 import DS18B20
import logging

app = FastAPI()
site = AdminSite(settings=Settings(database_url_async='sqlite+aiosqlite:///amisadmin.db'))
scheduler = SchedulerAdmin.bind(site)
data_queue = Queue()
loggers = {}


@app.get("/sensor/{log}")
def sensorData(log):
    with open(f"logs/{log}.log") as file:
        return PlainTextResponse(file.read())


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    while True:
        if not data_queue.empty():
            await ws.send_text(data_queue.get())


@scheduler.scheduled_job('interval', minutes=15)
def getTemps():
    sensors = DS18B20.get_all_sensors()
    for sensor in sensors:
        data = f"temp+{sensor.get_id()}:{sensor.get_temperature()}"
        data_queue.put(data)
        loggers["temp"].info(data)


@app.on_event("startup")
async def startup():
    scheduler.start()


def getLogger(filename: str):
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(message)s')

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


if __name__ == '__main__':
    loggers["temp"] = getLogger("logs/temp.log")

    site.mount_app(app)
    uvicorn.run(app, host="0.0.0.0", port=2002)
