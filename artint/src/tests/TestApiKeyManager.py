import asyncio
import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, src_dir)

from features.ApiKeyManager import ApiKeyManager
from datetime import datetime, timedelta, timezone

class TestApiKeyManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.api_keys = ['key1', 'key2', 'key3']
        self.manager = ApiKeyManager(self.api_keys)

    async def test_get_api_key_available(self):
        api_key = await self.manager.get_api_key()
        self.assertIn(api_key, self.api_keys)

    async def test_get_api_key_round_robin(self):
        keys_returned = []
        for _ in range(len(self.api_keys)):
            keys_returned.append(await self.manager.get_api_key())
        self.assertEqual(keys_returned, self.api_keys)
        # Next key should start from the beginning
        next_key = await self.manager.get_api_key()
        self.assertEqual(next_key, self.api_keys[0])

    async def test_mark_rate_limited_and_cleanup(self):
        api_key = self.api_keys[0]
        await self.manager.mark_rate_limited(api_key, 1)
        self.assertIn(api_key, self.manager.rate_limited_keys)
        
        # Wait for reset
        await asyncio.sleep(1.1)
        await self.manager.clean_rate_limited_keys()
        self.assertNotIn(api_key, self.manager.rate_limited_keys)

    async def test_get_next_available_time(self):
        now = datetime.now(timezone.utc)
        await self.manager.mark_rate_limited(self.api_keys[0], 10)
        await self.manager.mark_rate_limited(self.api_keys[1], 5)
        next_available = await self.manager.get_next_available_time()
        expected_time = now + timedelta(seconds=5)
        # Allow some tolerance in timing
        self.assertAlmostEqual(next_available.timestamp(), expected_time.timestamp(), delta=2)

if __name__ == '__main__':
    unittest.main()