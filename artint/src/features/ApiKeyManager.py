import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)

class ApiKeyManager:
    DAILY_LIMIT_PER_KEY = 5000  # URLScan daily limit per API key

    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_index = 0
        self.lock = asyncio.Lock()
        # Dictionary to store rate-limited keys and their reset timestamps
        self.rate_limited_keys = {}  # key: api_key, value: reset_timestamp
        self.total_possible_requests_today = len(api_keys) * self.DAILY_LIMIT_PER_KEY
        logging.info(f"ApiKeyManager.py: Maximum total requests per day: {self.total_possible_requests_today}")

    async def get_api_key(self):
        while True:
            async with self.lock:
                await self.clean_rate_limited_keys()
                api_key = self.find_available_api_key()
                if api_key:
                    logging.info(f'ApiKeyManager.py: Using URLScan API key index {self.current_index}')
                    return api_key
                else:
                    # All API keys are rate-limited
                    next_reset = await self.get_next_available_time()
                    sleep_duration = (next_reset - datetime.now(timezone.utc)).total_seconds()
                    if sleep_duration > 0:
                        logging.error(f"ApiKeyManager.py: All API keys are rate-limited. Waiting for {sleep_duration:.2f} seconds until reset.")
                    else:
                        sleep_duration = 1
            await asyncio.sleep(sleep_duration)

    async def clean_rate_limited_keys(self):
        now = datetime.now(timezone.utc)
        keys_to_remove = [api_key for api_key, reset_time in self.rate_limited_keys.items() if reset_time <= now]
        for api_key in keys_to_remove:
            del self.rate_limited_keys[api_key]
            logging.info(f"ApiKeyManager.py: API key {api_key} is no longer rate-limited.")

    def find_available_api_key(self):
        num_keys = len(self.api_keys)
        for _ in range(num_keys):
            api_key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % num_keys  # Circular array
            if api_key not in self.rate_limited_keys:
                return api_key
        return None  # All API keys are rate-limited

    async def mark_rate_limited(self, api_key, reset_after_seconds):
        async with self.lock:
            reset_time = datetime.now(timezone.utc) + timedelta(seconds=reset_after_seconds)
            self.rate_limited_keys[api_key] = reset_time
            logging.info(f"ApiKeyManager.py: API key {api_key} marked as rate-limited until {reset_time}.")

    async def get_next_available_time(self):
        async with self.lock:
            if not self.rate_limited_keys:
                return datetime.now(timezone.utc)
            next_reset = min(self.rate_limited_keys.values())
            return next_reset

    # Unused for now
    async def get_remaining_requests(self):
        remaining_requests = {}
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_remaining_requests(session, api_key) for api_key in self.api_keys]
            results = await asyncio.gather(*tasks)
            for api_key, remaining in results:
                remaining_requests[api_key] = remaining
        return remaining_requests

    async def fetch_remaining_requests(self, session, api_key):
        url = "https://urlscan.io/user/quotas/"
        headers = {
            "Content-Type": "application/json",
            "API-Key": api_key
        }
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logging.error(f"Failed to get quotas for API key {api_key}: HTTP {response.status}")
                    return (api_key, None)
                data = await response.json()
                remaining = data.get('limits', {}).get('public', {}).get('day', {}).get('remaining', None)
                logging.info(f"Remaining public requests for API key {api_key}: {remaining}")
                return (api_key, remaining)
        except Exception as e:
            logging.error(f"Exception while fetching quotas for API key {api_key}: {e}")
            return (api_key, None)
