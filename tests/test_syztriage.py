#!/usr/bin/env python3

import unittest
import src.syztriage as syztriage

BUG_EXAMPLE = "https://syzkaller.appspot.com/bug?extid=aeb14e2539ffb6d21130"


class TestSyzTriage(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.syz = syztriage.SyzTriage()

    def test_triage_syzkaller_bugs(self):
        self.assertTrue(self.syz.triage_syzkaller_bugs())


if __name__ == "__main__":
    unittest.main()
