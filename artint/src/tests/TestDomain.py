import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, src_dir)

from features.Domain import Domain
from unittest.mock import patch, MagicMock

class TestDomain(unittest.TestCase):
    def test_get_name_servers(self):
        mock_whois = MagicMock()
        mock_whois.name_servers = ['ns1.example.com', 'ns2.example.com']
        self.assertEqual(Domain.get_name_servers(mock_whois), 'ns1.example.com, ns2.example.com')

    def test_get_TLD(self):
        mock_whois = MagicMock()
        mock_whois.domain_name = 'example.com'
        with patch('tldextract.extract') as mock_extract:
            mock_extract.return_value.suffix = 'com'
            self.assertEqual(Domain.get_TLD(mock_whois), 'com')

    def test_get_registrar(self):
        mock_whois = MagicMock()
        mock_whois.registrar = 'Example Registrar Inc.'
        self.assertEqual(Domain.get_registrar(mock_whois), 'Example Registrar Inc.')

    def test_get_whois_server(self):
        mock_whois = MagicMock()
        mock_whois.whois_server = 'whois.example.com'
        self.assertEqual(Domain.get_whois_server(mock_whois), 'whois.example.com')

    def test_get_creation_date(self):
        mock_whois = MagicMock()
        mock_whois.creation_date.strftime.return_value = '01/01/2020, 12:00:00'
        self.assertEqual(Domain.get_creation_date(mock_whois), '01/01/2020, 12:00:00')

    def test_get_expiration_date(self):
        mock_whois = MagicMock()
        mock_whois.expiration_date.strftime.return_value = '01/01/2025, 12:00:00'
        self.assertEqual(Domain.get_expiration_date(mock_whois), '01/01/2025, 12:00:00')

    def test_get_updated_date(self):
        mock_whois = MagicMock()
        mock_whois.updated_date = [MagicMock()]
        mock_whois.updated_date[0].strftime.return_value = '04/04/2023, 12:00:00'
        self.assertEqual(Domain.get_updated_date(mock_whois), '04/04/2023, 12:00:00')

    def test_get_dnssec(self):
        mock_whois = MagicMock()
        mock_whois.dnssec = 'unsigned'
        self.assertEqual(Domain.get_dnssec(mock_whois), 'unsigned')

    @patch('dns.resolver.resolve')
    def test_get_a_record(self, mock_resolve):
        mock_resolve.return_value = ['93.184.216.34']
        self.assertEqual(Domain.get_a_record('example.com'), '93.184.216.34')

    @patch('dns.resolver.resolve')
    def test_get_aaaa_record(self, mock_resolve):
        mock_resolve.return_value = ['2606:2800:220:1:248:1893:25c8:1946']
        self.assertEqual(Domain.get_aaaa_record('example.com'), '2606:2800:220:1:248:1893:25c8:1946')

    @patch('dns.resolver.resolve')
    def test_get_mx_record(self, mock_resolve):
        mock_resolve.return_value = ['10 mail1.example.com.', '20 mail2.example.com.']
        self.assertEqual(Domain.get_mx_record('example.com'), '10 mail1.example.com., 20 mail2.example.com.')

    @patch('dns.resolver.resolve')
    def test_get_cname_record(self, mock_resolve):
        mock_resolve.return_value = ['cname.example.com.']
        self.assertEqual(Domain.get_cname_record('www.example.com'), 'cname.example.com.')

    @patch('dns.resolver.resolve')
    def test_get_ns_record(self, mock_resolve):
        mock_resolve.return_value = ['ns1.example.com.', 'ns2.example.com.']
        self.assertEqual(Domain.get_ns_record('example.com'), 'ns1.example.com., ns2.example.com.')

if __name__ == '__main__':
    unittest.main()