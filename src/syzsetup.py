#!/usr/bin/env python3

import logging

from src.syzcommon import SyzCommon


class SyzSetup(SyzCommon):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def check_kernel_repository(self, dry_run=False):
        pass

    def setup_kernel_config(self, dry_run=False):
        pass

    def build_kernel(self, dry_run=False):
        pass

    def run_vm(self, dry_run=False):
        pass

    def build_repro(self, dry_run=False):
        pass

    def push_repro(self, dry_run=False):
        pass

    def run_repro(self, dry_run=False):
        pass

