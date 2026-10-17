import unittest
from urllib.error import HTTPError, URLError

from vat_app.updater import UpdateError, check_for_update, is_newer, parse_version


class TestVersion(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("v0.10.2"), (0, 10, 2))
        self.assertEqual(parse_version("1.2"), (1, 2))
        self.assertEqual(parse_version("v1.0.0-beta"), (1, 0, 0))
        with self.assertRaises(UpdateError):
            parse_version("abc")

    def test_compare(self):
        self.assertTrue(is_newer("v0.4.0", "0.3.0"))
        self.assertTrue(is_newer("v0.10.0", "0.9.9"))  # so sánh số, không so chữ
        self.assertFalse(is_newer("v0.3.0", "0.3.0"))
        self.assertFalse(is_newer("0.3", "0.3.0"))
        self.assertFalse(is_newer("v0.2.9", "0.3.0"))


class TestCheck(unittest.TestCase):
    def test_not_configured(self):
        with self.assertRaises(UpdateError):
            check_for_update(repo="")

    def test_newer_release(self):
        fetch = lambda url: {"tag_name": "v0.4.0", "html_url": "https://github.com/a/b/releases/tag/v0.4.0"}
        info = check_for_update(repo="a/b", current="0.3.0", fetch=fetch)
        self.assertTrue(info.has_update)
        self.assertEqual(info.latest, "0.4.0")
        self.assertIn("v0.4.0", info.url)

    def test_up_to_date(self):
        info = check_for_update(repo="a/b", current="0.3.0", fetch=lambda url: {"tag_name": "v0.3.0"})
        self.assertFalse(info.has_update)

    def test_url_uses_repo(self):
        seen = []
        check_for_update(repo="khiem/cong-cu", current="0.3.0",
                         fetch=lambda url: seen.append(url) or {"tag_name": "v0.3.0"})
        self.assertEqual(seen, ["https://api.github.com/repos/khiem/cong-cu/releases/latest"])

    def test_network_errors_become_friendly_messages(self):
        def offline(url):
            raise URLError("no network")

        def not_found(url):
            raise HTTPError(url, 404, "Not Found", None, None)

        with self.assertRaisesRegex(UpdateError, "Internet"):
            check_for_update(repo="a/b", fetch=offline)
        with self.assertRaisesRegex(UpdateError, "Chưa có bản phát hành"):
            check_for_update(repo="a/b", fetch=not_found)


if __name__ == "__main__":
    unittest.main()
