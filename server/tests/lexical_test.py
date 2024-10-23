from phishnet.blueprints.features.Lexical import Lexical
import pytest

def test_count_digits():
    assert Lexical.count_digits("123abc") == 3
    assert Lexical.count_digits("abc") == 0
    assert Lexical.count_digits("") == 0

def test_count_digits_exception():
    assert Lexical.count_digits(lambda x:x) is None

def test_count_letters():
    assert Lexical.count_letters("123abc") == 3
    assert Lexical.count_letters("123") == 0
    assert Lexical.count_letters("") == 0

def test_count_letters_exception():
    assert Lexical.count_letters(lambda x:x) is None

def test_uses_https():
    assert Lexical.uses_https("https") == 1
    assert Lexical.uses_https("http") == 0

def test_shannon_entropy():
    assert Lexical.shannon_entropy("abc") is not None
    assert Lexical.shannon_entropy("") == 0

def test_shannon_entropy_exception():
    assert Lexical.shannon_entropy(lambda x:x) is None

def test_contains_ip_address():
    assert Lexical.contains_ip_address("192.168.1.1") == 1
    assert Lexical.contains_ip_address("www.example.com") == 0

def test_relative_entropy():
    assert Lexical.relative_entropy("") == None

def test_alphabet_entropy():
    assert Lexical.alphabet_entropy("test") == 1.5

def test_alphabet_entropy_exception():
    assert Lexical.alphabet_entropy(lambda x:x) is None

def test_count_sub():
    assert Lexical.count_sub(lambda x:x,lambda x:x) is None

def test_no_of_directories():
    assert Lexical.no_of_directories(lambda x:x) is None

def test_character_continuity_rate():
    assert Lexical.character_continuity_rate(lambda x:x) is None

def test_component_ratio_exceptions():
    assert Lexical.component_ratio(None, None) == 0
    assert Lexical.component_ratio("test", None) == 0 
    assert Lexical.component_ratio(lambda x: x, "test") is None

def test_extract_method():
    lexical = Lexical()
    url = 'https://www.example.com/path/to/resource?query=123#fragment'
    
    features = lexical.extract(url)
    
    assert features['url'] == url
    assert features['lexical_len_url'] == len(url)
    assert features['lexical_len_netloc'] == len('www.example.com')
    assert features['lexical_len_path'] == len('/path/to/resource')
    assert features['lexical_count_digits_netloc'] == 0
    assert features['lexical_count_letters_netloc'] == 13
    assert features['lexical_use_https'] == 1