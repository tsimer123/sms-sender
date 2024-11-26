import asyncio
import json

from aiohttp import ClientSession

from data_classes.data_request import GetResponseModel


class BaseRequest:
    def __init__(self, session: ClientSession, host: str, login_in: str, pass_in: str):
        self.session = session
        self.host = host
        self.login_in = login_in
        self.pass_in = pass_in

    @staticmethod
    def create_heders_auth() -> dict:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        return headers

    @staticmethod
    def create_heders_def() -> dict:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        return headers

    @staticmethod
    def create_heders_jsonrpc() -> dict:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        return headers

    @staticmethod
    def set_default_result() -> GetResponseModel:
        result = GetResponseModel(
            status=False,
        )
        return result

    async def get_auth(self) -> GetResponseModel:
        result = self.set_default_result()
        url = f'http://{self.host}/cgi-bin/luci/?luci_username={self.login_in}&luci_password={self.pass_in}'
        headers = self.create_heders_auth()

        try:
            resp = await asyncio.wait_for(
                self.session.post(url, allow_redirects=False, headers=headers),
                timeout=120,
            )
            if resp.ok and resp.status < 400 and 'sysauth_http' in resp.cookies:
                result.data = resp.cookies['sysauth_http'].value
                result.status = True
        except Exception as ex:
            result.error = ex.args
        return result

    async def get_request_sms_metod(self, metod: str, ts: str) -> GetResponseModel:
        headers = self.create_heders_def()
        result = self.set_default_result()
        url = f'http://{self.host}/cgi-bin/luci/admin/network/modem/modem1/sms?method={metod}&{ts}'

        try:
            resp = await asyncio.wait_for(
                self.session.get(url, headers=headers),
                timeout=120,
            )
            result.data = await resp.text()
            if resp.ok and resp.status < 400:
                result.data = json.loads(await resp.text())
                result.status = True
        except Exception as ex:
            result.error = ex.args
        return result

    async def get_request_sms_metod_params(self, metod: str, params_in: str, ts: str) -> GetResponseModel:
        headers = self.create_heders_def()
        result = self.set_default_result()
        url = f'http://{self.host}/cgi-bin/luci/admin/network/modem/modem1/sms?method={metod}&params={params_in}&{ts}'

        try:
            resp = await asyncio.wait_for(
                self.session.get(url, headers=headers),
                timeout=120,
            )
            result.data = await resp.text()
            if resp.ok and resp.status < 400:
                result.data = json.loads(await resp.text())
                result.status = True
        except Exception as ex:
            result.error = ex.args
        return result

    async def get_request_jsonrpc(self, jsonrpc: dict, ts: str) -> GetResponseModel:
        headers = self.create_heders_jsonrpc()
        result = self.set_default_result()
        url = f'http://{self.host}/ubus/?{ts}'
        jsonrpc = json.dumps(jsonrpc)

        try:
            resp = await asyncio.wait_for(
                self.session.post(url, data=jsonrpc, headers=headers),
                timeout=120,
            )
            result.data = await resp.text()
            if resp.ok and resp.status < 400:
                result.data = json.loads(await resp.text())
                result.status = True
        except Exception as ex:
            result.error = ex.args
        return result
