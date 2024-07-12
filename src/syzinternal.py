#!/usr/bin/env python3

import os
import logging

INTERNAL_BUGS = {
    "KERN-48": "34afb82a3c67",
    "KERN-49": "34afb82a3c67",
    "KERN-51": "34afb82a3c67",
    "KERN-52": "34afb82a3c67",
    "KERN-53": "34afb82a3c67",
    "KERN-55": "34afb82a3c67",
    "KERN-56": "34afb82a3c67",
    "KERN-57": "34afb82a3c67",
    "KERN-58": "34afb82a3c67",
    "KERN-60": "34afb82a3c67",
}

INTERNAL_CONFIG = ("https://syzkaller.appspot.com/text?tag=KernelConfig&x="
                   "c3820d4fff43c7a3")

# Terminal formatting
RED = "\033[31m"
ENDC = '\033[0m'


class SyzInternal():
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def get_internal_bug_details(self, dry_run=False):
        """
        Retrieves details of internal bugs, including repository URLs,
        commit IDs, configuration URLs, and C reproducer URIs.

        Parameters:
        dry_run (bool): If True, simulates the retrieval of bug details without
                        making any changes(default is False).

        Returns:
        list: A list of dictionaries containing bug details if successful or
              if dry_run is True. Each dictionary contains the keys 'repo_url',
              'commit', 'config_url', 'c_repro_uri', and 'task_name'.
        None: False if a required C reproducer file does not exist. If no valid
              crashes are found.
        """
        valid_crashes = []
        if dry_run:
            return [{"repo_url": ("https://git.kernel.org/pub/scm/linux/kernel"
                                  "/git/torvalds/linux.git/log/?id=45db3ab7009"
                                  "2637967967bfd8e6144017638563c"),
                     "commit": "45db3ab70092",
                     "config_url": INTERNAL_CONFIG,
                     "c_repro_uri": "internal-repro/repro-KERN-X.c",
                     "task_name": "KERNX"}]

        for bug in INTERNAL_BUGS:
            repro_c_path = os.path.join("internal-repro", f"repro-{bug}.c")
            self.logger.debug(f"repro C path: {repro_c_path}")
            if not os.path.exists(repro_c_path):
                self.logger.error(f"{RED}C reproducer for {bug} does not"
                                  f" exist. Should be placed in "
                                  f"{repro_c_path}{ENDC}")
                return None
            valid_crashes.append({
                "repo_url": ("https://git.kernel.org/pub/scm/linux/kernel"
                             "/git/torvalds/linux.git/log/?id="
                             f"{INTERNAL_BUGS[bug]}"),
                "commit": INTERNAL_BUGS[bug],
                "config_url": INTERNAL_CONFIG,
                "c_repro_uri": repro_c_path,
                "task_name": bug
            })

        if not valid_crashes:
            self.logger.error(f"{RED}No valid crashes found!{ENDC}")
            return None
        return valid_crashes
