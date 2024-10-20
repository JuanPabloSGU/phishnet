import asyncio
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)

class ApiKeyManager:
    """
    Manages a set of URLScan API keys, ensuring that each key respects its daily request limit.
    It handles the distribution of API keys for making requests and manages rate-limiting
    by tracking when each key can be reused after hitting its limit.
    """
    DAILY_LIMIT_PER_KEY = 5000  # URLScan daily limit per API key

    def __init__(self, api_keys):
        """
        Initializes the ApiKeyManager with a list of URLScan API keys.

        Parameters:
        api_keys (list): A list of URLScan API key strings to be managed.
        """
        self.api_keys = api_keys # List of available API keys
        self.current_index = 0 # Index to track the next API key to use
        self.lock = asyncio.Lock() # Lock to ensure thread-safe operations
        # Dictionary to store rate-limited keys and their reset timestamps
        self.rate_limited_keys = {}  # key: api_key, value: reset_timestamp
        self.total_possible_requests_today = len(api_keys) * self.DAILY_LIMIT_PER_KEY
        logging.info(f"ApiKeyManager.py: Maximum total requests per day: {self.total_possible_requests_today}")

    async def get_api_key(self):
        """
        Retrieves an available URLScan API key that is not currently rate-limited.
        If all keys are rate-limited, it waits until the next key becomes available.

        Returns:
        str: An available URLScan API key.
        """
        while True:
            async with self.lock:
                # Clean up any keys that are no longer rate-limited
                await self.clean_rate_limited_keys()
                # Attempt to find an available API key
                api_key = self.find_available_api_key()
                if api_key:
                    logging.info(f'ApiKeyManager.py: Using URLScan API key index {self.current_index}')
                    return api_key
                else:
                    # All API keys are rate-limited
                    next_reset = await self.get_next_available_time()
                    # Calculate how long to wait until the next key becomes available
                    sleep_duration = (next_reset - datetime.now(timezone.utc)).total_seconds()
                    if sleep_duration > 0:
                        logging.error(f"ApiKeyManager.py: All API keys are rate-limited. Waiting for {sleep_duration:.2f} seconds until reset.")
                    else:
                        # If the calculated sleep duration is negative or zero, set a minimal wait time
                        sleep_duration = 1
            await asyncio.sleep(sleep_duration)

    async def clean_rate_limited_keys(self):
        """
        Removes URLScan API keys from the rate-limited list if their reset time has passed.
        """
        now = datetime.now(timezone.utc)
        # Identify keys whose rate-limiting period has ended
        keys_to_remove = [api_key for api_key, reset_time in self.rate_limited_keys.items() if now >= reset_time]
        for api_key in keys_to_remove:
            del self.rate_limited_keys[api_key]
            logging.info(f"ApiKeyManager.py: API key {api_key} is no longer rate-limited.")

    def find_available_api_key(self):
        """
        Finds the next available URLScan API key that is not currently rate-limited.

        Returns:
        str or None: An available URLScan API key if one exists; otherwise, None.
        """
        num_keys = len(self.api_keys)
        for _ in range(num_keys):
            # Select the API key at the current index
            api_key = self.api_keys[self.current_index]
            # Move to the next index in a circular manner
            self.current_index = (self.current_index + 1) % num_keys
            # Check if the selected API key is not rate-limited
            if api_key not in self.rate_limited_keys:
                return api_key
        # All API keys are currently rate-limited
        return None

    async def mark_rate_limited(self, api_key, reset_after_seconds):
        """
        Marks a URLScan API key as rate-limited and sets its reset time.

        Parameters:
        api_key (str): The URLScan API key to be rate-limited.
        reset_after_seconds (int): The number of seconds after which the key can be used again.
        """
        async with self.lock:
            # Calculate the exact time when the API key will be available again
            reset_time = datetime.now(timezone.utc) + timedelta(seconds=reset_after_seconds)
            self.rate_limited_keys[api_key] = reset_time
            logging.info(f"ApiKeyManager.py: API key {api_key} marked as rate-limited until {reset_time}.")

    async def get_next_available_time(self):
        """
        Determines the next time at which an API key will become available.

        Returns:
        datetime: The earliest reset time among all rate-limited API keys.
        """
        async with self.lock:
            if not self.rate_limited_keys:
                # If no keys are rate-limited, return the current time
                return datetime.now(timezone.utc)
            # Find the minimum reset time among all rate-limited keys
            next_reset = min(self.rate_limited_keys.values())
            return next_reset