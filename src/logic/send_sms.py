import datetime
import json
import logging
import time
from asyncio import Queue, sleep
from urllib.parse import quote

from aiohttp import ClientSession, CookieJar
from pytz import timezone

from config import dif_korrect, file_log, send_sleep
from data_classes.data_base import TaskIn, TaskSms
from http_base import BaseRequest

log_file = logging.FileHandler(file_log)
console_out = logging.StreamHandler()
logging.basicConfig(
    handlers=(log_file, console_out), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s'
)


async def send_sms(task_rb: TaskSms, command_queue: Queue):
    logging.info(f': {task_rb.name}: start kroks {task_rb.ip}')
    cookiejar = CookieJar(unsafe=True)
    async with ClientSession(cookie_jar=cookiejar) as session:
        con = BaseRequest(
            session,
            task_rb.ip,
            task_rb.login,
            task_rb.passw,
        )
        # получаем токен авторизации
        auth = await con.get_auth()
        logging.info(f': {task_rb.name}: start task hand')
        if auth.status is True:
            time_info = await get_time_kroks(task_rb, con, auth.data)
            logging.info(f': {task_rb.name}: true auth kroks {task_rb.ip}')
            status_queue = False
            while status_queue is False:
                status_queue = command_queue.empty()
                logging.info(f': {task_rb.name}: start status_queue = {status_queue}')
                if status_queue is False:
                    task = await command_queue.get()
                    logging.info(f': {task_rb.name}: получено из очереди заданий - {len(task)}')
                    await handler_command(task_rb, con, time_info, task)
                    command_queue.task_done()
                    status_queue = command_queue.empty()
                    logging.info(f': {task_rb.name}: stop status_queue = {status_queue}')
                    if status_queue is False:
                        logging.info(
                            f': {task_rb.name}: sleep after working off a pack, if the line is not empty: {send_sleep} sec'
                        )
                        await sleep(send_sleep)

    logging.info(f': {task_rb.name}: stop kroks {task_rb.ip}')


async def handler_command(task_rb: TaskSms, con: BaseRequest, time_info: dict, command: list[TaskIn]):
    send_result = []
    for count_sim, sim in enumerate(command):
        logging.info(f': {task_rb.name}: start number tel {sim.phone_number}')
        logging.info(f': {task_rb.name}: handler_command: count_sim={count_sim} start number tel {sim.phone_number}')
        tz = timezone(time_info['timezone'])
        len_sim = len(command)
        send_result.append({'phone_number': sim.phone_number, 'command': sim.command, 'ts_send': '', 'status': False})
        logging.info(f': {task_rb.name}: start number tel {sim.phone_number}')
        ts_send = round(datetime.datetime.now(tz=tz).timestamp() * 1000)
        send_result[count_sim]['ts_send'] = round(ts_send / 1000)
        logging.info(f": {task_rb.name}: gen ts_send {send_result[count_sim]['ts_send']}")
        metod = 'create'
        params = f"'{sim.phone_number}','{sim.command}'"
        temp_result = await con.get_request_sms_metod_params(metod, quote(params), ts_send)
        send_result[count_sim]['status'] = temp_result.status
        logging.info(f': {task_rb.name}: {temp_result.status} end number tel {sim.phone_number}')
        if count_sim < len_sim - 1:
            logging.info(f': {task_rb.name}: sleep {send_sleep} sec')
            await sleep(send_sleep)

    logging.info(f': {task_rb.name}: stop task hand')
    logging.info(f': {task_rb.name}: start check task')
    ts = str(round(time.time() * 1000))
    metod = 'list'
    get_send_sms = await con.get_request_sms_metod(metod, ts)
    if get_send_sms.status is True:
        parse_result_send_sms(task_rb, get_send_sms.data, send_result)
    logging.info(f': {task_rb.name}: stop check task')


async def get_time_kroks(task_rb: TaskSms, con: BaseRequest, token: str) -> dict:
    logging.info(f': {task_rb.name}: get info kroks')
    ts_send = round(datetime.datetime.now().timestamp() * 1000)
    jsonrps = [
        {'id': 0, 'jsonrpc': '2.0', 'method': 'call', 'params': [token, 'system', 'info', {}]},
        {'id': 1, 'jsonrpc': '2.0', 'method': 'call', 'params': [token, 'luci', 'getTimezones', {}]},
    ]
    info = await con.get_request_jsonrpc(jsonrps, str(ts_send))
    tzstring = None
    for tz_val in info.data[1]['result'][1].values():
        if 'active' in tz_val:
            tzstring = tz_val['tzstring']
    if tzstring is None:
        raise Exception(f': {task_rb.name}: Часовой пояс на кроксе должен быть: Europe/Moscow, tzstring: "MSK-3"')
    logging.info(f': {task_rb.name}: localtime host {round(ts_send/1000)}')
    logging.info(f': {task_rb.name}: localtime kroks {info.data[0]["result"][1]["localtime"]}')
    logging.info(
        f': {task_rb.name}: localtime dif {(info.data[0]["result"][1]["localtime"] - 10800) - round(ts_send/1000)}'
    )
    result = {
        'localtime': info.data[0]['result'][1]['localtime'] - 10800,
        'tzstring': 'MSK-3',
        'timezone': 'Europe/Moscow',
    }
    return result


def parse_result_send_sms(task_rb: TaskSms, data: dict, send_result: list[dict]):
    for task in send_result:
        trigger_task = 0
        for key, val in data['result'].items():
            if task['phone_number'] == key:
                for sms in val:
                    ts_sms = int(sms['storage']['properties']['timestamp'])
                    if (
                        ((task['ts_send'] - dif_korrect) <= ts_sms <= (task['ts_send'] + dif_korrect))
                        and sms['storage']['properties']['state'] == 'sent'
                        and sms['storage']['content']['text'] == task['command']
                    ):
                        logging.info(
                            f': {task_rb.name}: number: {task["phone_number"]} command: {task["command"]} ts_send: {task["ts_send"]} kroks_send: {ts_sms} - true'
                        )
                        trigger_task = 1
                        break
        if trigger_task == 0:
            logging.info(f': {task_rb.name}: NOT TASK MATCH {task}')
            logging.info(f': {task_rb.name}: all send sms {json.dumps(data)}')
            print(1)
