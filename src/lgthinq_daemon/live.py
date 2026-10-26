"""Lazily own the HTTP session on the backend's asyncio loop."""

import logging

from .client import BackendError, SDKClient
from .credentials import Vault


class LiveClient:
    def __init__(self, *, account, country, client_id, allow_control=False):
        self.account, self.country, self.client_id = account, country, client_id
        self.allow_control = allow_control
        self.session = None
        self.adapter = None

    async def _get(self):
        if self.adapter is None:
            from aiohttp import ClientSession
            from thinqconnect.thinq_api import ThinQApi

            token = Vault().read(self.account)
            logging.getLogger("thinqconnect").setLevel(logging.CRITICAL)
            self.session = ClientSession()
            api = ThinQApi(
                session=self.session,
                access_token=token,
                country_code=self.country,
                client_id=self.client_id,
            )
            self.adapter = SDKClient(api, allow_control=self.allow_control)
        return self.adapter

    async def discover(self):
        return await (await self._get()).discover()

    async def profile(self, device_id):
        return await (await self._get()).profile(device_id)

    async def status(self, device_id):
        return await (await self._get()).status(device_id)

    async def control(self, device_id, payload):
        if not self.allow_control:
            raise BackendError("real_control_not_authorized")
        await (await self._get()).control(device_id, payload)

    async def close(self):
        if self.session:
            await self.session.close()
