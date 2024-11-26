import logging
from asyncio import Queue
from urllib.parse import quote

from config import file_log, pull_modem, step_pack
from data_classes.data_base import TaskIn, TaskSms
from excel import open_excel
from logic.send_sms import send_sms

log_file = logging.FileHandler(file_log)
console_out = logging.StreamHandler()
logging.basicConfig(
    handlers=(log_file, console_out), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s'
)


def create_command(name_file: str = 'task.xlsx') -> list[TaskIn]:
    result = None

    data = open_excel(name_file)

    if len(data) > 0:
        result = []
        for command in data:
            if len(command) >= 2:
                try:
                    result.append(TaskIn(phone_number=str(command[0]), command=command[1]))
                except Exception as ex:
                    print(ex)
            else:
                raise Exception(f'Не верное количество параметров в задании {command}')
    else:
        raise Exception(f'Нет заданий в файле {name_file}')

    return result


async def send_kroks_queue(kroks_queue: Queue, command_queue: Queue):
    while True:
        command = await kroks_queue.get()
        await send_sms(command, command_queue)
        kroks_queue.task_done()


async def customer_generator_from_excel(kroks_queue: Queue, command_queue: Queue):
    command = create_command()
    len_command = len(command)
    logging.info(f'from Excel get count command: {len_command}')

    for kroks in pull_modem:
        task = TaskSms(name=kroks['name'], ip=kroks['ip'], login=kroks['login'], passw=quote(kroks['pass']))
        await kroks_queue.put(task)

    if len(command) > 0:
        count_uqipment_q = 0
        for i in range(0, len_command, step_pack):
            await command_queue.put(command[i : i + step_pack])
            count_uqipment_q += 1
        logging.info(f'added parts commands in queue - {count_uqipment_q}')
    else:
        logging.info('not task for handlers')
    logging.info('stop customer_generator_from_excel')
