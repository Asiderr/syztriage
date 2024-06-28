#!/usr/bin/env python3

import logging
import os

from src.syzcommon import SyzCommon

PREFIX_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/"
LTS_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
UPSTREAM_REMOTE = (
    "https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git"
)

# Terminal formatting
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
ENDC = '\033[0m'


class SyzSetup(SyzCommon):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def _check_kernel_remote(self, repo_path: str, remote_uri: str,
                             dry_run=False):
        """
        """
        try:
            self.check_git_version(dry_run=dry_run)
        except FileNotFoundError:
            return False

        if not os.path.exists(repo_path) and not dry_run:
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            self.logger.error(f"{RED}Kernel check has failed!{ENDC}")
            return False

        repo_name = remote_uri.split(PREFIX_REMOTE)[1].split(".git")[0]
        self.logger.debug(f"Repository name: {repo_name}")
        if self.check_repository_remote(repo_path, repo_name,
                                        dry_run=dry_run):
            self.logger.debug(f"Repository remote exists: {remote_uri}")
            return True

        self.logger.debug("Repository remote doesn't exist. "
                          f"Adding new remote: {remote_uri}")
        if not self.add_repository_remote(repo_path, remote_uri, repo_name,
                                          dry_run=dry_run):
            return False
        self.remote_name = repo_name
        return True

    def _setup_kernel_config(self, repo_path: str, config_uri, dry_run=False):
        """
        """
        cmd_download_config = ["curl", config_uri, "-o", ".config"]
        self.logger.debug("CMD: " + " ".join(cmd_download_config))

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not self.run_cmd(cmd_download_config,
                            f"{RED}Downloading kernel config failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        os.chdir(workspace_dir)
        return True

    def setup_kernel_repository(self, crash_dict: dict, repo_path,
                                dry_run=False):
        """
        """
        if "stable/linux" in crash_dict["repo_url"]:
            remote_uri = LTS_REMOTE
        elif "torvalds/linux" in crash_dict["repo_url"]:
            remote_uri = UPSTREAM_REMOTE
        else:
            self.logger.error(f"{RED}Linux repository not supported! Currently"
                              " script supports only the upstream and"
                              f" LTS{ENDC}.")
            return False

        if not self._check_kernel_remote(repo_path, remote_uri,
                                         dry_run=dry_run):
            self.logger.error(f"{RED}Setting kernel remote failed!{ENDC}")
            return False

        if not self.remote_name:
            self.logger.error(f"{RED}Remote name not set! It should be set"
                              f" by _check_kernel_remote.{ENDC}")
            return False

        if not self.fetch_repository_remote(repo_path, self.remote_name,
                                            dry_run=dry_run):
            self.logger.error(f"{RED}Fetching kernel remote failed!{ENDC}")
            return False

        if not self.checkout_branch(repo_path, crash_dict["commit"],
                                    dry_run=dry_run):
            self.logger.error(f"{RED}Kernel checkout failed!{ENDC}")
            return False

        if not self._setup_kernel_config(repo_path, crash_dict["config_url"],
                                         dry_run=dry_run):
            self.logger.error(f"{RED}Fetching kernel config failed!{ENDC}")
            return False
        return True

    # reporduce bug class
    def build_kernel(self, dry_run=False):
        pass

    def run_vm(self, dry_run=False):
        pass

    def build_c_repro(self, dry_run=False):
        pass

    def push_c_repro(self, dry_run=False):
        pass

    def run_c_repro(self, dry_run=False):
        pass
