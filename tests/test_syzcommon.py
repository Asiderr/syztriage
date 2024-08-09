#!/usr/bin/env python3
import logging
import unittest
import src.syzcommon as syzcommon

TEST_REPO_URI = "https://github.com/Asiderr/syztriage.git"
TEST_REPO_DIR = "syztriage"


class TestSyzCommon(unittest.TestCase):
    def setUp(self) -> None:
        self.syz = syzcommon.SyzCommon()
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.syz.clone_repository(TEST_REPO_URI)
        return super().setUp()

    def tearDown(self) -> None:
        self.syz.remove_repository(TEST_REPO_DIR)
        return super().tearDown()

    def test_check_repository_remote_valid_remote(self):
        self.assertTrue(
            self.syz.check_repository_remote(TEST_REPO_DIR,
                                             "Asiderr/syztriage")
        )
        self.assertEqual(self.syz.remote_name, "origin")

    def test_check_repository_remote_invalid_remote(self):
        self.assertFalse(
            self.syz.check_repository_remote(TEST_REPO_DIR, "INVALID_REMOTE")
        )
        self.assertIsNone(self.syz.remote_name)

    def test_check_repository_remote_invalid_repo_path(self):
        self.assertFalse(
            self.syz.check_repository_remote("INVALID_PATH", "INVALID_REMOTE")
        )
        self.assertIsNone(self.syz.remote_name)

    def test_check_repository_remote_not_repo_path(self):
        self.assertFalse(
            self.syz.check_repository_remote("~", "INVALID_REMOTE")
        )
        self.assertIsNone(self.syz.remote_name)


if __name__ == "__main__":
    unittest.main()
