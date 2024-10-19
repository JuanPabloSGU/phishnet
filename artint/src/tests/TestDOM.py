import os
import sys
import unittest
from unittest.mock import AsyncMock, patch
import importlib

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, src_dir)

from features.ApiKeyManager import ApiKeyManager
from features.DOM import DOM

class TestDOM(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = AsyncMock(spec=importlib.import_module('aiohttp').ClientSession)
        self.mock_api_key_manager = AsyncMock(spec=ApiKeyManager)

        patcher = patch('features.DOM.generate_user_agent', return_value='TestUserAgent/1.0')
        self.mock_generate_user_agent = patcher.start()
        self.addCleanup(patcher.stop)
        self.dom = DOM(session=self.mock_session, api_key_manager=self.mock_api_key_manager)
        self.base_expected_feat_dict = {
            'url': 'https://www.example.com',
            'dom_total_nodes': -1,
            'dom_max_depth': -1,
            'dom_average_depth': -1,
            'dom_unique_tags': -1,
            'dom_num_comments': -1,
            'dom_has_canvas': -1,
            'dom_has_video': -1,
            'dom_has_audio': -1,
            'dom_total_attributes': -1,
            'dom_average_attributes': -1,
            'dom_inline_event_handlers': -1,
            'dom_deprecated_tags_used': -1,
            'dom_num_script_tags': -1,
            'dom_screenshot_url': '-1'
        }
    
    async def test_extract_successful(self):
        url = 'https://www.example.com'
        uuid = 'test-uuid'
        dom_content = '<html><head></head><body><script></script></body></html>'
        
        with patch.object(self.dom, 'submit_url', return_value=uuid) as mock_submit_url, \
             patch.object(self.dom, 'get_result', return_value={'result_key': 'result_value'}) as mock_get_result, \
             patch.object(self.dom, 'get_dom_snapshot', return_value=dom_content) as mock_get_snapshot, \
             patch.object(self.dom, 'extract_dom_features', return_value=None) as mock_extract_features:

            result = await self.dom.extract(url)
            
            # Assertions
            mock_submit_url.assert_awaited_once_with(url)
            mock_get_result.assert_awaited_once_with(uuid, retries=5)
            mock_get_snapshot.assert_awaited_once_with(uuid, retries=5)
            mock_extract_features.assert_awaited_once_with(dom_content)
            expected_result = self.base_expected_feat_dict.copy()
            expected_result['dom_screenshot_url'] = f"https://urlscan.io/screenshots/{uuid}.png"
            self.assertEqual(result, expected_result)
    
    @patch('features.DOM.DOM.submit_url')
    async def test_extract_submit_url_failure(self, mock_submit_url):
        url = 'https://www.example.com'
        mock_submit_url.return_value = None
        result = await self.dom.extract(url)

        mock_submit_url.assert_awaited_once_with(url)
        self.assertEqual(result, self.base_expected_feat_dict)
    
    @patch('features.DOM.DOM.submit_url')
    @patch('features.DOM.DOM.get_result')
    async def test_extract_get_result_failure(self, mock_get_result, mock_submit_url):
        url = 'https://www.example.com'
        uuid = 'test-uuid'

        mock_submit_url.return_value = uuid
        mock_get_result.return_value = None
        result = await self.dom.extract(url)
        
        # Assertions
        mock_submit_url.assert_awaited_once_with(url)
        mock_get_result.assert_awaited_once_with(uuid, retries=5)
        self.assertEqual(result, self.base_expected_feat_dict)
    
    @patch('features.DOM.DOM.submit_url')
    @patch('features.DOM.DOM.get_result')
    @patch('features.DOM.DOM.get_dom_snapshot')
    async def test_extract_get_dom_snapshot_failure(self, mock_get_snapshot, mock_get_result, mock_submit_url):
        url = 'https://www.example.com'
        uuid = 'test-uuid'

        mock_submit_url.return_value = uuid
        mock_get_result.return_value = {'result_key': 'result_value'}
        mock_get_snapshot.return_value = None
        result = await self.dom.extract(url)
        
        # Assertions
        mock_submit_url.assert_awaited_once_with(url)
        mock_get_result.assert_awaited_once_with(uuid, retries=5)
        mock_get_snapshot.assert_awaited_once_with(uuid, retries=5)
        self.assertEqual(result, self.base_expected_feat_dict)
    
    async def test_extract_dom_features(self):
        dom_content = """
        <html>
            <head>
                <title>Test Page</title>
                <script src="app.js"></script>
            </head>
            <body onload="init()" onerror="handleError()">
                <canvas></canvas>
                <video></video>
                <audio></audio>
                <div class="container">
                    <p>Paragraph</p>
                    <a href="#" onclick="clickHandler()">Link</a>
                    <applet></applet>
                </div>
            </body>
        </html>
        """

        self.dom.initialize_feat_dict(self.base_expected_feat_dict['url'])
        await self.dom.extract_dom_features(dom_content)
        
        # Assertions
        self.assertEqual(self.dom.feat_dict['dom_total_nodes'], 12)
        self.assertEqual(self.dom.feat_dict['dom_max_depth'], 5)
        self.assertAlmostEqual(self.dom.feat_dict['dom_average_depth'], 2.75, delta=0.4)
        self.assertEqual(self.dom.feat_dict['dom_unique_tags'], 12)
        self.assertEqual(self.dom.feat_dict['dom_num_comments'], 0)
        self.assertEqual(self.dom.feat_dict['dom_has_canvas'], 1)
        self.assertEqual(self.dom.feat_dict['dom_has_video'], 1)
        self.assertEqual(self.dom.feat_dict['dom_has_audio'], 1)
        self.assertEqual(self.dom.feat_dict['dom_total_attributes'], 6)
        self.assertAlmostEqual(self.dom.feat_dict['dom_average_attributes'], 7 / 12, delta=0.09)
        self.assertEqual(self.dom.feat_dict['dom_inline_event_handlers'], 3)
        self.assertEqual(self.dom.feat_dict['dom_deprecated_tags_used'], 1)
        self.assertEqual(self.dom.feat_dict['dom_num_script_tags'], 1)
    
    async def test_extract_dom_features_deprecated_tags(self):
        dom_content = """
        <html>
            <body>
                <applet></applet>
                <font></font>
                <center></center>
                <div></div>
            </body>
        </html>
        """
        
        self.dom.initialize_feat_dict(self.base_expected_feat_dict['url'])
        await self.dom.extract_dom_features(dom_content)
        self.assertEqual(self.dom.feat_dict['dom_deprecated_tags_used'], 3)
    
    async def test_extract_dom_features_inline_event_handlers(self):
        dom_content = """
        <html>
            <body onload="init()" onclick="handleClick()" onmouseover="hover()">
                <div></div>
            </body>
        </html>
        """
        
        self.dom.initialize_feat_dict(self.base_expected_feat_dict['url'])
        await self.dom.extract_dom_features(dom_content)
        self.assertEqual(self.dom.feat_dict['dom_inline_event_handlers'], 3)
    
if __name__ == '__main__':
    unittest.main()