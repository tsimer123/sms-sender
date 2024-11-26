import asyncio
from asyncio import Queue

from config import pull_modem
from creat_task import customer_generator_from_excel, send_kroks_queue


async def main():
    # task_in_excel = excel_get()
    # task = TaskSms(ip='192.168.190.132', login='root', passw=quote('L%3~E6Hk'), param_data=task_in_excel)
    # await send_sms(task)

    handler_count = len(pull_modem)

    kroks_queue = Queue(handler_count)
    command_queue = Queue(100)

    customer_producer = asyncio.create_task(customer_generator_from_excel(kroks_queue, command_queue))

    cashiers = [asyncio.create_task(send_kroks_queue(kroks_queue, command_queue)) for i in range(handler_count)]

    await asyncio.gather(customer_producer, *cashiers)


if __name__ in '__main__':
    asyncio.run(main())
