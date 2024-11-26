pull_modem = [
    {
        'name': 'chlb-kroks-3',
        'ip': '192.168.190.132',
        'login': 'root',
        'pass': 'L%3~E6Hk',
    },
    {
        'name': 'perm-kroks-1',
        'ip': '192.168.190.2',
        'login': 'root',
        'pass': 'Ehh~X8Bl',
    },
]

# задержка между отправками смс на одном роутере
send_sleep = 300  # в секундах, пол умолчанию не меньше 300

# диапазон секунд для поправки на запись timestamp в крокс
dif_korrect = 20

# имя файла для логов
file_log = 'py_log.log'

# количество команд в одной пачке
step_pack = 2
