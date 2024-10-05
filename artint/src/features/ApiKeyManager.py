import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)

class ApiKeyManager:
    def __init__(self, api_keys, rate_limit_reset_time=3600):
        self.api_keys = api_keys
        self.current_index = 0
        self.lock = asyncio.Lock()
        # Dictionary with key (API key) and value (timestamp when it was rate-limited)
        self.rate_limited_keys = {}
        self.rate_limit_reset_time = rate_limit_reset_time

    async def get_api_key(self):
        async with self.lock:
            now = time.time()
            # Clean up rate-limited keys that have passed the reset time
            keys_to_remove = []
            for api_key, timestamp in self.rate_limited_keys.items():
                if now - timestamp >= self.rate_limit_reset_time:
                    keys_to_remove.append(api_key)
            for api_key in keys_to_remove:
                del self.rate_limited_keys[api_key]

            # Find a non-rate-limited API key
            for _ in range(len(self.api_keys)):
                api_key = self.api_keys[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.api_keys) # Circular array
                if api_key not in self.rate_limited_keys:
                    logging.info(f'ApiKeyManager.py: Using URLScan API key index {self.current_index}')
                    return api_key

            # All API keys are rate-limited
            logging.error("ApiKeyManager.py: All API keys are rate-limited. Waiting for reset.")
            await asyncio.sleep(self.rate_limit_reset_time)
            return None

    async def mark_rate_limited(self, api_key):
        async with self.lock:
            self.rate_limited_keys[api_key] = time.time()
            logging.info(f"ApiKeyManager.py: API key {api_key} marked as rate-limited.")
