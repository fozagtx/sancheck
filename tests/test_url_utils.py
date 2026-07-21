import unittest

from sancheck.url_utils import extract_urls, normalize_url


class UrlUtilsTests(unittest.TestCase):
    def test_normalize_adds_https_and_idna(self):
        self.assertEqual(normalize_url("bücher.example/path"), "https://xn--bcher-kva.example/path")

    def test_extract_urls_dedupes_and_trims_punctuation(self):
        text = "Open https://example.com/a, then www.example.org/test. Again https://example.com/a"
        self.assertEqual(extract_urls(text), ["https://example.com/a", "https://www.example.org/test"])


if __name__ == "__main__":
    unittest.main()

