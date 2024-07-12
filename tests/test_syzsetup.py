#!/usr/bin/env python3
import logging
import os
import unittest
import src.syzsetup as syzsetup

TEST_REPO_URI = "https://github.com/Asiderr/syztriage.git"
TEST_REPO_DIR = "syztriage"
TEST_CONFIG_URI = (
    "https://syzkaller.appspot.com/text?tag=KernelConfig&x=617171361dd3cd47"
)
TEST_CRASH_DETAILS = {
    "repo_url": "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/log/?id=45db3ab70092637967967bfd8e6144017638563c",
    "commit": "45db3ab70092",
    "config_url": "https://syzkaller.appspot.com/text?tag=KernelConfig&x=617171361dd3cd47",
    "c_repro_uri": "https://syzkaller.appspot.com/text?tag=ReproC&x=112f45d4980000",
}


class TestSyzSetup(unittest.TestCase):
    def setUp(self) -> None:
        self.syz = syzsetup.SyzSetup()
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

    def test_check_kernel_remote_invalid_path(self):
        self.assertFalse(
            self.syz._check_kernel_remote("INVALID", syzsetup.LTS_REMOTE,
                                          dry_run=False)
        )

    def test_check_kernel_remote_dry_run(self):
        self.assertTrue(
            self.syz._check_kernel_remote("INVALID", syzsetup.LTS_REMOTE,
                                          dry_run=True)
        )

    def test_check_kernel_remote_valid_remote(self):
        self.syz.add_repository_remote(TEST_REPO_DIR, syzsetup.LTS_REMOTE,
                                       "lts")
        self.assertTrue(self.syz._check_kernel_remote(TEST_REPO_DIR,
                                                      syzsetup.LTS_REMOTE))
        self.assertEqual(self.syz.remote_name, "lts")

    def test_check_kernel_remote_non_existing_remote(self):
        self.assertTrue(self.syz._check_kernel_remote(TEST_REPO_DIR,
                                                      syzsetup.LTS_REMOTE))
        self.assertEqual(self.syz.remote_name, "stable/linux")

    def test_setup_kernel_config_dry_run(self):
        self.assertTrue(
            self.syz._setup_kernel_config(TEST_REPO_DIR, TEST_CONFIG_URI,
                                          dry_run=True)
        )

    def test_setup_kernel_config_invalid_path(self):
        self.assertFalse(
            self.syz._setup_kernel_config("INVALID", TEST_CONFIG_URI)
        )

    def test_setup_kernel_config_invalid_config_uri(self):
        self.assertFalse(
            self.syz._setup_kernel_config(TEST_REPO_DIR, "INVALID")
        )

    def test_setup_kernel_config_valid_config_uri(self):
        self.assertTrue(
            self.syz._setup_kernel_config(TEST_REPO_DIR, TEST_CONFIG_URI)
        )
        self.assertTrue(os.path.exists(f"{TEST_REPO_DIR}/.config"))

    def test_setup_kernel_repository_invalid_repo(self):
        crash_detail_invalid_repo = TEST_CRASH_DETAILS.copy()
        crash_detail_invalid_repo["repo_url"] = "INVALID"
        self.assertFalse(
            self.syz.setup_kernel_repository(crash_detail_invalid_repo,
                                             TEST_REPO_DIR)
        )

    def test_setup_kernel_repository_valid(self):
        self.assertTrue(
            self.syz.setup_kernel_repository(TEST_CRASH_DETAILS, TEST_REPO_DIR)
        )


if __name__ == "__main__":
    unittest.main()
