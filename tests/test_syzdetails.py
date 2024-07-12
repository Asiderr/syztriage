#!/usr/bin/env python3

import logging
import unittest
import src.syzdetails as syzdetails

NO_REPRO_URL = "https://syzkaller.appspot.com/bug?extid=fc5141fdfb1e59951d38"
VALID_URL = "https://syzkaller.appspot.com/bug?extid=aeb14e2539ffb6d21130"


class TestSyzDetails(unittest.TestCase):
    def setUp(self) -> None:
        self.syz = syzdetails.SyzDetails()
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        return super().setUp()

    def test_fetch_bug_report_invalid_url(self):
        try:
            self.syz._fetch_bug_report("INVALID URL")
            self.fail("Method should raise ConnectionError exception!")
        except ConnectionError:
            return

    def test_fetch_bug_report_invalid_site(self):
        try:
            self.syz._fetch_bug_report("google.com")
            self.fail("Method should raise exception!")
        except ValueError:
            return

    def test_fetch_bug_report_valid_site(self):
        bug_title = "<title>KMSAN: uninit-value in aes_encrypt (5)</title>"
        report = self.syz._fetch_bug_report(VALID_URL)
        self.assertTrue(bug_title in report)

    def test_fetch_bug_report_dry_run(self):
        self.assertIsNone(self.syz._fetch_bug_report(VALID_URL, dry_run=True))

    def test_find_crashes_invalid_html(self):
        bug_html = "Invalid"
        self.assertIsNone(self.syz._find_crashes(bug_html))

    def test_find_crashes_valid_html(self):
        bug_html = self.syz._fetch_bug_report(VALID_URL)
        crash_table = self.syz._find_crashes(bug_html)
        self.assertEqual("45db3ab70092", crash_table["Commit"][0][0])

    def test_analyze_crashes_no_repro(self):
        bug_html = self.syz._fetch_bug_report(NO_REPRO_URL)
        crash_table = self.syz._find_crashes(bug_html)
        self.assertFalse(self.syz._analyze_crashes(crash_table))

    def test_analyze_crashes_existing_repro(self):
        bug_html = self.syz._fetch_bug_report(
            VALID_URL
        )
        crash_table = self.syz._find_crashes(bug_html)
        valid_crashes = self.syz._analyze_crashes(crash_table)
        self.assertTrue(valid_crashes)
        self.assertEqual("45db3ab70092", valid_crashes[0]["commit"])

    def test_get_bug_details_existing_repro(self):
        valid_crashes = self.syz.get_bug_details(
                VALID_URL
            )
        self.assertTrue(valid_crashes)
        self.assertEqual("45db3ab70092", valid_crashes[0]["commit"])

    def test_get_bug_details_broken_url(self):
        self.assertIsNone(self.syz.get_bug_details("INVALID"))

    def test_get_bug_details_invaild_non_syzbot_url(self):
        self.assertIsNone(self.syz.get_bug_details("google.com"))

    def test_get_bug_details_invaild_syzbot_url(self):
        self.assertIsNone(
            self.syz.get_bug_details("https://syzkaller.appspot.com/upstream")
        )

    def test_get_bug_details_no_repro(self):
        self.assertIsNone(self.syz.get_bug_details(NO_REPRO_URL))

    def test_get_bug_details_dry_run(self):
        self.assertListEqual(
            self.syz.get_bug_details(VALID_URL, dry_run=True),
            [{"repo_url": ("https://git.kernel.org/pub/scm/linux/kernel"
                           "/git/torvalds/linux.git/log/?id=45db3ab7009"
                           "2637967967bfd8e6144017638563c"),
              "commit": "45db3ab70092",
              "config_url": ("https://syzkaller.appspot.com/text?tag=Ke"
                             "rnelConfig&x=617171361dd3cd47"),
              "c_repro_uri": ("https://syzkaller.appspot.com/text?tag=R"
                              "eproC&x=112f45d4980000")}])


if __name__ == "__main__":
    unittest.main()
