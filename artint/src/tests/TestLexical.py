import os
import sys
import unittest

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, src_dir)

from features.Lexical import Lexical
from math import log2

class TestLexical(unittest.TestCase):
    def test_count_digits(self):
        self.assertEqual(Lexical.count_digits('abc123'), 3)
        self.assertEqual(Lexical.count_digits('no_digits'), 0)
        self.assertEqual(Lexical.count_digits('123456'), 6)

    def test_count_letters(self):
        self.assertEqual(Lexical.count_letters('abc123'), 3)
        self.assertEqual(Lexical.count_letters('123456'), 0)
        self.assertEqual(Lexical.count_letters('ABCdef'), 6)

    def test_component_ratio(self):
        self.assertAlmostEqual(Lexical.component_ratio(3, 'abcdef'), 0.5)
        self.assertEqual(Lexical.component_ratio('abc', 'abcdef'), 0.5)
        self.assertEqual(Lexical.component_ratio(0, 'abcdef'), 0)

    def test_uses_https(self):
        self.assertEqual(Lexical.uses_https('https'), 1)
        self.assertEqual(Lexical.uses_https('http'), 0)
        self.assertEqual(Lexical.uses_https('ftp'), 0)

    def test_shannon_entropy(self):
        # 'aabbcc' entropy: 1.585
        expected_entropy = -(3 * (2/6) * log2(2/6))
        self.assertAlmostEqual(Lexical.shannon_entropy('aabbcc'), expected_entropy, places=3)
        
        # 'abc' entropy: 1.585
        expected_entropy = -(3 * (1/3) * log2(1/3))
        self.assertAlmostEqual(Lexical.shannon_entropy('abc'), expected_entropy, places=3)
        
        # 'aaaaaa' entropy: 0
        self.assertEqual(Lexical.shannon_entropy('aaaaaa'), -0.0)

    def test_alphabet_entropy(self):
        # 'example' has e:2, x:1, a:1, m:1, p:1, l:1
        expected_entropy = -( (2/7)*log2(2/7) + 5*(1/7)*log2(1/7) )
        self.assertAlmostEqual(Lexical.alphabet_entropy('example'), expected_entropy, places=3)
        
        # 'abcABC' entropy: 2 distinct lowercase and 2 distinct uppercase
        expected_entropy = -(6 * (1/6) * log2(1/6))
        self.assertAlmostEqual(Lexical.alphabet_entropy('abcABC'), expected_entropy, places=3)
        
        # Non-alphabetic characters are ignored
        self.assertAlmostEqual(Lexical.alphabet_entropy('a1b2c3'), -(3 * (1/3) * log2(1/3)), places=3)

    def test_count_sub(self):
        self.assertEqual(Lexical.count_sub('hello.world', '.'), 1)
        self.assertEqual(Lexical.count_sub('user@domain.com', '@'), 1)
        self.assertEqual(Lexical.count_sub('https://embed.example.com', '//'), 1)

    def test_no_of_directories(self):
        self.assertEqual(Lexical.no_of_directories('/a/b/c'), 3)
        self.assertEqual(Lexical.no_of_directories('/a/b'), 2)
        self.assertEqual(Lexical.no_of_directories('/a/b/c/'), 4)

    def test_contains_ip_address(self):
        self.assertEqual(Lexical.contains_ip_address('192.168.1.1'), 1)
        self.assertEqual(Lexical.contains_ip_address('example.com'), 0)
        self.assertEqual(Lexical.contains_ip_address('123.456.78.90:8080'), 0)

    def test_character_continuity_rate(self):
        self.assertAlmostEqual(Lexical.character_continuity_rate('aaabbb'), 0.333, delta=0.001)
        self.assertEqual(Lexical.character_continuity_rate('aabbaa'), 0.5)
        self.assertEqual(Lexical.character_continuity_rate('abcdef'), 0)

if __name__ == '__main__':
    unittest.main()