import unittest
from unittest.mock import AsyncMock
from ServiceUtils import preprocess_url, deduplicate_batch, check_failure
import aiohttp

class TestUtils(unittest.IsolatedAsyncioTestCase):
    #region preprocess_url
    async def test_preprocess_url_https_success(self):
        url = 'example.com'
        session = AsyncMock()
        session.head = AsyncMock(return_value=AsyncMock(status=200))
        
        result = await preprocess_url(session, url)
        self.assertEqual(result, 'https://example.com')

    async def test_preprocess_url_https_failure_http_success(self):
        url = 'example.com'
        session = AsyncMock()
        # First HTTPS attempt fails
        session.head.side_effect = [aiohttp.ClientError(), AsyncMock(status=200)]
        
        result = await preprocess_url(session, url)
        self.assertEqual(result, 'http://example.com')

    async def test_preprocess_url_both_fail(self):
        url = 'example.com'
        session = AsyncMock()
        # Both HTTPS and HTTP attempts fail
        session.head.side_effect = [aiohttp.ClientError(), aiohttp.ClientError()]
        
        result = await preprocess_url(session, url)
        self.assertIsNone(result)

    async def test_preprocess_url_with_scheme(self):
        url = 'https://example.com'
        session = AsyncMock()
        session.head = AsyncMock(return_value=AsyncMock(status=200))
        
        result = await preprocess_url(session, url)
        self.assertEqual(result, 'https://example.com')
    #endregion

    #region deduplicate_batch
    def test_deduplicate_batch_no_duplicates(self):
        docs = [
            {'url': 'http://example.com'},
            {'url': 'http://example.org'}
        ]
        result = deduplicate_batch(docs)
        self.assertEqual(len(result), 2)

    def test_deduplicate_batch_with_duplicates(self):
        docs = [
            {'url': 'http://example.com'},
            {'url': 'http://example.com/'},
            {'url': 'http://example.org'},
            {'url': 'http://example.org/'}
        ]
        result = deduplicate_batch(docs)
        self.assertEqual(len(result), 2)

    def test_deduplicate_batch_empty(self):
        docs = []
        result = deduplicate_batch(docs)
        self.assertEqual(len(result), 0)

    def test_deduplicate_batch_mixed(self):
        docs = [
            {'url': 'http://example.com'},
            {'url': 'http://example.com/path'},
            {'url': 'http://example.com'},
            {'url': 'http://example.com/path/'}
        ]
        result = deduplicate_batch(docs)
        self.assertEqual(len(result), 2)
    #endregion

    #region check_failure
    def test_check_failure_no_failures(self):
        feature_dict = {'feature1': 1, 'feature2': 2, 'feature3': 3}
        result = check_failure(feature_dict)
        self.assertFalse(result, "Should return False when there are no failures")

    def test_check_failure_all_failures(self):
        feature_dict = {'feature1': -1, 'feature2': -1, 'feature3': -1}
        result = check_failure(feature_dict)
        self.assertTrue(result, "Should return True when all features have failed")

    def test_check_failure_half_failures(self):
        feature_dict = {'feature1': -1, 'feature2': -1, 'feature3': 1, 'feature4': 2}
        result = check_failure(feature_dict)
        self.assertTrue(result, "Should return True when failed features are >= 50%")

    def test_check_failure_less_than_half_failures(self):
        feature_dict = {'feature1': -1, 'feature2': 1, 'feature3': 2, 'feature4': 3}
        result = check_failure(feature_dict)
        self.assertFalse(result, "Should return False when failed features are < 50%")

    def test_check_failure_non_numeric_failures(self):
        feature_dict = {'feature1': "-1", 'feature2': "-1", 'feature3': 1, 'feature4': 2}
        result = check_failure(feature_dict)
        self.assertTrue(result, "Should return True when half or more features failed")

    def test_check_failure_mixed_failure_values(self):
        feature_dict = {'feature1': "-1", 'feature2': -1, 'feature3': "-1", 'feature4': -1}
        result = check_failure(feature_dict)
        self.assertTrue(result, "Should return True when all failure values are '-1' or -1")

    def test_check_failure_empty_dict(self):
        feature_dict = {}
        result = check_failure(feature_dict)
        self.assertFalse(result, "Should return False when the feature dict is empty")
    #endregion

if __name__ == '__main__':
    unittest.main()