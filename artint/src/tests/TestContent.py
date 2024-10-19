import aiohttp
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import importlib
from bs4 import BeautifulSoup

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, src_dir)

from features.Content import Content

class TestContent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_session = AsyncMock(spec=aiohttp.ClientSession)
        patcher = patch('features.Content.generate_user_agent', return_value='TestUserAgent/1.0')
        self.mock_generate_user_agent = patcher.start()
        self.addCleanup(patcher.stop)
        
        self.content = Content(session=self.mock_session)
        
        self.base_expected_feat_dict = {
            'url': 'https://www.example.com',
            'content_redirects': -1,
            'content_len_html': -1,
            'content_len_text': -1,
            'content_len_links': -1,
            'content_len_mail_usage_forms': -1,
            'content_meta_script_link_percentage': '-1',
            'content_mouseover_changes': -1,
            'content_right_click_disabled': -1,
            'content_keyboard_shortcuts_disabled': -1,
            'content_copy_paste_disabled': -1,
            'content_drag_drop_disabled': -1,
            'content_popup_window_has_text_field': -1,
            'content_use_iframe': -1,
            'content_use_upload': -1,
            'content_use_download': -1,
            'content_use_http_link': -1
        }

    async def test_extract_successful(self):
        url = 'https://www.example.com'
        response_data = {
            'content': b'<html><head></head><body><a href="#">Link</a></body></html>',
            'redirects': 1
        }
        
        # Setup mocks
        with patch.object(self.content, 'make_request', return_value=response_data) as mock_make_request:
            result = await self.content.extract(url)
            
            # Assertions
            mock_make_request.assert_awaited_once_with(url, timeout=15, retries=3)
            self.assertEqual(result['url'], url)
            self.assertEqual(result['content_redirects'], response_data['redirects'])
            self.assertEqual(result['content_len_html'], len(BeautifulSoup(response_data['content'], 'html.parser').prettify()))
            self.assertEqual(result['content_len_text'], len(BeautifulSoup(response_data['content'], 'html.parser').get_text()))
            self.assertEqual(result['content_len_links'], 1)
            self.assertEqual(result['content_len_mail_usage_forms'], 0)
            self.assertEqual(result['content_meta_script_link_percentage'], "0, 0, 0")
            self.assertEqual(result['content_mouseover_changes'], 0)
            self.assertEqual(result['content_right_click_disabled'], 0)
            self.assertEqual(result['content_keyboard_shortcuts_disabled'], 0)
            self.assertEqual(result['content_copy_paste_disabled'], 0)
            self.assertEqual(result['content_drag_drop_disabled'], 0)
            self.assertEqual(result['content_popup_window_has_text_field'], 0)
            self.assertEqual(result['content_use_iframe'], 0)
            self.assertEqual(result['content_use_upload'], 0)
            self.assertEqual(result['content_use_download'], 0)
            self.assertEqual(result['content_use_http_link'], 0)

    async def test_extract_make_request_failure(self):
        url = 'https://www.example.com'
        response_data = None
        with patch.object(self.content, 'make_request', return_value=response_data) as mock_make_request:
            result = await self.content.extract(url)
            
            # Assertions
            mock_make_request.assert_awaited_once_with(url, timeout=15, retries=3)
            self.assertEqual(result, self.base_expected_feat_dict)

    async def test_make_request_success(self):
        url = 'https://www.example.com'
        response_mock = AsyncMock()
        response_mock.status = 200
        response_mock.history = [MagicMock()]
        response_mock.read = AsyncMock(return_value=b'<html></html>')
        response_mock.raise_for_status = MagicMock()
        response_mock.__aenter__.return_value = response_mock
        
        # Mock 'session.get' to return the response_mock in an async context manager
        self.mock_session.get.return_value = response_mock
        result = await self.content.make_request(url, timeout=15, retries=3)
        
        # Assertions
        self.mock_session.get.assert_called_once_with(url, timeout=15, allow_redirects=True)
        self.assertEqual(result, {'content': b'<html></html>', 'redirects': 1})

    async def test_make_request_client_error(self):
        url = 'https://www.example.com'
        self.mock_session.get.side_effect = aiohttp.ClientError()
        result = await self.content.make_request(url, timeout=15, retries=3)
        self.assertIsNone(result)

    async def test_get_links(self):
        html_content = """
        <html>
            <body>
                <a href="#">Link1</a>
                <a href="#">Link2</a>
                <a href="#">Link3</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        link_count = self.content.get_links(soup)
        self.assertEqual(link_count, 3)

    async def test_get_mail_usage_form(self):
        # Test with mailto in form
        html_content = """
        <html>
            <body>
                <form action="mailto:test@example.com">
                    <input type="submit" value="Send">
                </form>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        mail_usage = self.content.get_mail_usage_form(soup)
        self.assertEqual(mail_usage, 1)
        
        # Test without mailto
        html_content_no_mail = """
        <html>
            <body>
                <form action="/submit">
                    <input type="submit" value="Submit">
                </form>
            </body>
        </html>
        """
        soup_no_mail = BeautifulSoup(html_content_no_mail, 'html.parser')
        mail_usage_no = self.content.get_mail_usage_form(soup_no_mail)
        self.assertEqual(mail_usage_no, 0)

    async def test_get_mouseover_changes(self):
        # Test with mouseover changing window.status
        html_content = """
        <html>
            <body>
                <div onmouseover="window.status='Hovering'"></div>
                <div onmouseover="doSomething()"></div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        mouseover_changes = self.content.get_mouseover_changes(soup)
        self.assertEqual(mouseover_changes, 1)
        
        # Test without mouseover changing window.status
        html_content_no_changes = """
        <html>
            <body>
                <div onmouseover="doSomething()"></div>
            </body>
        </html>
        """
        soup_no_changes = BeautifulSoup(html_content_no_changes, 'html.parser')
        mouseover_no_changes = self.content.get_mouseover_changes(soup_no_changes)
        self.assertEqual(mouseover_no_changes, 0)

    async def test_get_right_click_disabled(self):
        # Test with right-click disabled
        html_content = """
        <html>
            <head>
                <script>
                    document.oncontextmenu = function() { event.button==2 };
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        right_click = self.content.get_right_click_disabled(soup)
        self.assertEqual(right_click, 1)
        
        # Test without right-click disabled
        html_content_no_disable = """
        <html>
            <head>
                <script>
                    console.log("No disable");
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_no_disable = BeautifulSoup(html_content_no_disable, 'html.parser')
        right_click_no = self.content.get_right_click_disabled(soup_no_disable)
        self.assertEqual(right_click_no, 0)

    async def test_get_keyboard_shortcuts_disabled(self):
        """Test get_keyboard_shortcuts_disabled method."""
        # Test Case 1: Keyboard shortcuts disabled via keydown
        html_content_keydown = """
        <html>
            <head>
                <script>
                    window.addEventListener('keydown', function(event) {
                        event.preventDefault();
                    });
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_keydown = BeautifulSoup(html_content_keydown, 'html.parser')
        keyboard_disabled = self.content.get_keyboard_shortcuts_disabled(soup_keydown)
        self.assertEqual(keyboard_disabled, 1, "Should detect keydown event with preventDefault() and return 1")
        
        # Test Case 2: Keyboard shortcuts not disabled
        html_content_no_keyboard_disable = """
        <html>
            <head>
                <script>
                    console.log("No keyboard shortcuts disabled");
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_no_keyboard_disable = BeautifulSoup(html_content_no_keyboard_disable, 'html.parser')
        keyboard_not_disabled = self.content.get_keyboard_shortcuts_disabled(soup_no_keyboard_disable)
        self.assertEqual(keyboard_not_disabled, 0, "Should not detect keyboard shortcuts disabled and return 0")
        
        # Test Case 3: Keyboard shortcuts disabled via keypress
        html_content_keypress = """
        <html>
            <head>
                <script>
                    document.onkeypress = function(event) {
                        event.preventDefault();
                    };
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_keypress = BeautifulSoup(html_content_keypress, 'html.parser')
        keyboard_disabled_keypress = self.content.get_keyboard_shortcuts_disabled(soup_keypress)
        self.assertEqual(keyboard_disabled_keypress, 1, "Should detect keypress event with preventDefault() and return 1")

    async def test_get_copy_paste_disabled(self):
        """Test get_copy_paste_disabled method."""
        # Test Case 1: Copy-paste disabled via copy event
        html_content_copy = """
        <html>
            <head>
                <script>
                    window.addEventListener('copy', function(event) {
                        event.preventDefault();
                    });
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_copy = BeautifulSoup(html_content_copy, 'html.parser')
        copy_paste_disabled = self.content.get_copy_paste_disabled(soup_copy)
        self.assertEqual(copy_paste_disabled, 1, "Should detect copy event with preventDefault() and return 1")
        
        # Test Case 2: Copy-paste not disabled
        html_content_no_copy_disable = """
        <html>
            <head>
                <script>
                    console.log("No copy-paste disabled");
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_no_copy_disable = BeautifulSoup(html_content_no_copy_disable, 'html.parser')
        copy_paste_not_disabled = self.content.get_copy_paste_disabled(soup_no_copy_disable)
        self.assertEqual(copy_paste_not_disabled, 0, "Should not detect copy-paste disabled and return 0")
        
        # Test Case 3: Copy-paste disabled via paste event
        html_content_paste = """
        <html>
            <head>
                <script>
                    document.onpaste = function(event) {
                        event.preventDefault();
                    };
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_paste = BeautifulSoup(html_content_paste, 'html.parser')
        copy_paste_disabled_paste = self.content.get_copy_paste_disabled(soup_paste)
        self.assertEqual(copy_paste_disabled_paste, 1, "Should detect paste event with preventDefault() and return 1")

    async def test_get_drag_drop_disabled(self):
        """Test get_drag_drop_disabled method."""
        # Test Case 1: Drag-drop disabled via dragstart event
        html_content_dragstart = """
        <html>
            <head>
                <script>
                    window.addEventListener('dragstart', function(event) {
                        event.preventDefault();
                    });
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_dragstart = BeautifulSoup(html_content_dragstart, 'html.parser')
        drag_drop_disabled = self.content.get_drag_drop_disabled(soup_dragstart)
        self.assertEqual(drag_drop_disabled, 1, "Should detect dragstart event with preventDefault() and return 1")
        
        # Test Case 2: Drag-drop not disabled
        html_content_no_drag_disable = """
        <html>
            <head>
                <script>
                    console.log("No drag-drop disabled");
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_no_drag_disable = BeautifulSoup(html_content_no_drag_disable, 'html.parser')
        drag_drop_not_disabled = self.content.get_drag_drop_disabled(soup_no_drag_disable)
        self.assertEqual(drag_drop_not_disabled, 0, "Should not detect drag-drop disabled and return 0")
        
        # Test Case 3: Drag-drop disabled via drop event
        html_content_drop = """
        <html>
            <head>
                <script>
                    document.ondrop = function(event) {
                        event.preventDefault();
                    };
                </script>
            </head>
            <body>
                <p>Test</p>
            </body>
        </html>
        """
        soup_drop = BeautifulSoup(html_content_drop, 'html.parser')
        drag_drop_disabled_drop = self.content.get_drag_drop_disabled(soup_drop)
        self.assertEqual(drag_drop_disabled_drop, 1, "Should detect drop event with preventDefault() and return 1")

    async def test_popup_window_has_text_field(self):
        # Test with popup window having text field
        html_content = """
        <html>
            <body>
                <div class="popup">
                    <input type="text" name="username">
                </div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        popup_with_text = self.content.popup_window_has_text_field(soup)
        self.assertEqual(popup_with_text, 1)
        
        # Test without popup window having text field
        html_content_no_text = """
        <html>
            <body>
                <div class="popup">
                    <input type="password" name="password">
                </div>
            </body>
        </html>
        """
        soup_no_text = BeautifulSoup(html_content_no_text, 'html.parser')
        popup_without_text = self.content.popup_window_has_text_field(soup_no_text)
        self.assertEqual(popup_without_text, 0)

    async def test_use_iframe(self):
        # Test with iframe usage
        html_content = """
        <html>
            <body>
                <iframe src="frame.html"></iframe>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        use_iframe = self.content.use_iframe(soup)
        self.assertEqual(use_iframe, 1)
        
        # Test without iframe usage
        html_content_no_iframe = """
        <html>
            <body>
                <p>No iframe here</p>
            </body>
        </html>
        """
        soup_no_iframe = BeautifulSoup(html_content_no_iframe, 'html.parser')
        use_iframe_no = self.content.use_iframe(soup_no_iframe)
        self.assertEqual(use_iframe_no, 0)

    async def test_use_upload(self):
        # Test with upload input
        html_content = """
        <html>
            <body>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file">
                    <input type="submit" value="Upload">
                </form>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        use_upload = self.content.use_upload(soup)
        self.assertEqual(use_upload, 1)
        
        # Test without upload input
        html_content_no_upload = """
        <html>
            <body>
                <form action="/submit" method="post">
                    <input type="text" name="username">
                    <input type="submit" value="Submit">
                </form>
            </body>
        </html>
        """
        soup_no_upload = BeautifulSoup(html_content_no_upload, 'html.parser')
        use_upload_no = self.content.use_upload(soup_no_upload)
        self.assertEqual(use_upload_no, 0)

    async def test_use_download(self):
        # Test with download link
        html_content = """
        <html>
            <body>
                <a href="file.zip" download>Download</a>
                <a href="http://example.com">Link</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        use_download = self.content.use_download(soup)
        self.assertEqual(use_download, 1)
        
        # Test without download link
        html_content_no_download = """
        <html>
            <body>
                <a href="http://example.com">Link1</a>
                <a href="http://example.org">Link2</a>
            </body>
        </html>
        """
        soup_no_download = BeautifulSoup(html_content_no_download, 'html.parser')
        use_download_no = self.content.use_download(soup_no_download)
        self.assertEqual(use_download_no, 0)

    async def test_use_http_link(self):
        # Test with http link
        html_content = """
        <html>
            <body>
                <a href="http://example.com">HTTP Link</a>
                <a href="https://secure.com">HTTPS Link</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        use_http_link = self.content.use_http_link(soup)
        self.assertEqual(use_http_link, 1)
        
        # Test without http link
        html_content_no_http = """
        <html>
            <body>
                <a href="https://secure.com">HTTPS Link1</a>
                <a href="https://secure.org">HTTPS Link2</a>
            </body>
        </html>
        """
        soup_no_http = BeautifulSoup(html_content_no_http, 'html.parser')
        use_http_link_no = self.content.use_http_link(soup_no_http)
        self.assertEqual(use_http_link_no, 0)

    async def test_meta_script_link_percentage(self):
        # Test with meta, script, and link tags
        html_content = """
        <html>
            <head>
                <meta charset="UTF-8">
                <meta name="description" content="Test">
                <script src="app.js"></script>
                <script>
                    console.log("Hello");
                </script>
                <link rel="stylesheet" href="styles.css">
                <link rel="icon" href="favicon.ico">
            </head>
            <body>
                <a href="#">Link</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        percentages = self.content.meta_script_link_percentage(soup)
        actual_values = [float(p.strip()) for p in percentages.split(',')]
        
        # Define expected values
        expected_values = [0.0, 0.33, 0.66]
        
        # Perform assertions using assertAlmostEqual
        for actual, expected in zip(actual_values, expected_values):
            self.assertAlmostEqual(actual, expected, delta=0.01, msg=f"Expected {expected}, got {actual}")
        
        # Test with no meta, script, or link tags
        html_content_no_links = "<html><body><p>No links here</p></body></html>"
        soup_no_links = BeautifulSoup(html_content_no_links, 'html.parser')
        percentages_no_links = self.content.meta_script_link_percentage(soup_no_links)
        self.assertEqual(percentages_no_links, "0, 0, 0")

if __name__ == '__main__':
    unittest.main()