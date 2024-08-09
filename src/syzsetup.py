#!/usr/bin/env python3

import logging
import multiprocessing
import os

from src.syzcommon import SyzCommon

PREFIX_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/"
LTS_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git"
BFP_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/bpf/bpf.git"
NET_REMOTE = "https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git"
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
        Checks and manages the remote repository configuration for the kernel.

        Parameters:
        repo_path (str): The local path to the kernel repository.
        remote_uri (str): The URI of the remote repository.
        dry_run (bool): If True, simulates the entire process without making
                        any changes (default is False).

        Returns:
        bool: True if the remote repository is successfully configured or
              if dry_run is True, False otherwise.
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
        Sets up the kernel configuration file for a specified repository.

        Parameters:
        repo_path (str): The local path to the kernel repository.
        config_uri (str): The URI from which to download the kernel
                          configuration file.
        dry_run (bool): If True, simulates the entire process without making
                        any changes (default is False).

        Returns:
        bool: True if the kernel configuration file is successfully set up
              or if dry_run is True, False otherwise.
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

    def _build_kernel(self, repo_path, dry_run=False):
        """
        Builds the kernel using specified configuration and build commands.

        Parameters:
        repo_path (str): The local path to the kernel repository.
        dry_run (bool): If True, simulates the entire build process without
                        making any changes (default is False).

        Returns:
        bool: True if the kernel build is successful or if dry_run is True,
              False otherwise.
        """
        nproc = multiprocessing.cpu_count()
        cmd_kernel_conf = ["make", f"-j{nproc}", "LLVM=1", "LLVM_IAS=1",
                           'CC=ccache clang', "ARCH=x86_64", "olddefconfig"]
        cmd_build_kernel = ["make", f"-j{nproc}", "LLVM=1", "LLVM_IAS=1",
                            'CC=ccache clang', "ARCH=x86_64", "all",
                            "compile_commands.json"]

        self.logger.debug("CMD: " + " ".join(cmd_kernel_conf))
        self.logger.debug("CMD: " + " ".join(cmd_build_kernel))
        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not os.path.exists(".config"):
            self.logger.error(f"{RED}Kernel config does not exist!{ENDC}")

        if not self.run_cmd(cmd_kernel_conf,
                            f"{RED}Creating kernel config failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        if not self.run_cmd(cmd_build_kernel,
                            f"{RED}Building kernel failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        os.chdir(workspace_dir)
        return True

    def setup_kernel_repository(self, crash_dict: dict, repo_path,
                                dry_run=False):
        """
        Sets up a kernel repository for reproducing a crash.

        Parameters:
        crash_dict (dict): A dictionary containing crash details, including:
            - "repo_url": URL of the kernel repository.
            - "commit": Commit hash to checkout.
            - "config_url": URL to fetch the kernel configuration file.
        repo_path (str): The local path to the kernel repository.
        dry_run (bool): If True, simulates the entire setup process without
                        making any changes (default is False).

        Returns:
        bool: True if the kernel repository is successfully set up or if
              dry_run is True, False otherwise.
        """
        if "stable/linux" in crash_dict["repo_url"]:
            remote_uri = LTS_REMOTE
        elif "torvalds/linux" in crash_dict["repo_url"]:
            remote_uri = UPSTREAM_REMOTE
        elif "netdev/net" in crash_dict["repo_url"]:
            remote_uri = NET_REMOTE
        elif "bpf/bpf" in crash_dict["repo_url"]:
            remote_uri = BFP_REMOTE
        else:
            self.logger.error(f"{RED}Repository is not supported! Currently"
                              " script supports only the upstream, bfp, net,"
                              " and LTS Linux repositories.{ENDC}")
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

        if not self._build_kernel(repo_path, dry_run=dry_run):
            self.logger.error(f"{RED}Building kernel failed!{ENDC}")
            return False
        return True
