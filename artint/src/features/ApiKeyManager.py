import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)

class AllApiKeysRateLimited(Exception):
    pass

class ApiKeyManager:
    DAILY_LIMIT_PER_KEY = 5000  # URLScan daily limit per API key

    def __init__(self, api_keys, rate_limit_reset_time=60):
        self.api_keys = api_keys
        self.current_index = 0
        self.lock = asyncio.Lock()
        # Dictionary with key (API key) and value (timestamp when it was rate-limited)
        self.rate_limited_keys = {}
        self.rate_limit_reset_time = rate_limit_reset_time
        self.total_possible_requests_today = len(api_keys) * self.DAILY_LIMIT_PER_KEY
        logging.info(f"ApiKeyManager.py: Maximum total requests per day: {self.total_possible_requests_today}")

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
            raise AllApiKeysRateLimited("All API keys are rate-limited or have exhausted their daily limits.")

    async def mark_rate_limited(self, api_key):
        async with self.lock:
            self.rate_limited_keys[api_key] = time.time()
            logging.info(f"ApiKeyManager.py: API key {api_key} marked as rate-limited.")
