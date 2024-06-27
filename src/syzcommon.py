#!/usr/bin/env python3

import logging
import subprocess
import sys
import os

# Terminal formatting
RED = "\033[31m"
ENDC = '\033[0m'


class SyzCommon:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def run_cmd(self, cmd, err_msg, dump_std=False):
        """
        Execute a command in the system shell.

        Args:
            cmd (list):         The command to be executed.
            err_msg (str):      The error message to be logged if the
                                command fails.
            dump_std (bool):    The flag indicates if stdout of the command
                                should be dumped to the variables

        Returns:
        bool:              True if the command execution is successful (return
                           code 0), False otherwise.
        self.output (str): Standard output of the command.
        """
        self.stdout = ""
        if not dump_std:
            p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
            p.wait()
        else:
            p = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = p.communicate()
            self.stdout = stdout.decode("utf-8")
            self.stderr = stderr.decode("utf-8")

        if p.returncode != 0:
            self.logger.error(err_msg)
            return False
        return True

    def check_git_version(self, dry_run=False):
        """
        Check if git is installed.

        Args:
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If command
                           was successful returns True, if not it returns False
        """
        cmd_version = ["git", "--version"]
        self.logger.debug("CMD: " + " ".join(cmd_version))

        if dry_run:
            return True

        try:
            if not self.run_cmd(cmd_version,
                                f"{RED}git version check failed!{ENDC}",
                                dump_stdout=True):
                return False
            if self.stdout:
                self.logger.debug(self.stdout)
            else:
                return False
        except FileNotFoundError:
            self.logger.error(f"{RED}git command not available!{ENDC}")
            return False

        return True

    def checkout_branch(self, branch, dry_run=False):
        """
        """
        cmd_checkout = ["git", "checkout", branch]
        err_msg = "doesn't exist in the repository."
        self.logger.debug("CMD: " + " ".join(cmd_checkout))

        if dry_run:
            return True

        if not self.run_cmd(cmd_checkout,
                            f"{RED}{branch} {err_msg}!{ENDC}"):
            return False
        return True

    def add_repository_remote(self, repo_dir, remote_uri, remote_name,
                              dry_run=False):
        """
        Check if git add new repository remote.

        Args:
            repo_dir (str):    A repository relative directory where a new
                               remote will be added
            remote_uri (str):  A remote uri to be added
            remote_name (str): Name of the new remote
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If adding
                           remote was successful returns True, if not it
                           returns False
        """
        cmd_remote_add = ["git", "remote", "add", remote_name, remote_uri]
        cmd_fetch_remote = ["git", "fetch", remote_name]
        self.logger.debug("CMD: " + " ".join(cmd_remote_add))
        self.logger.debug("CMD: " + " ".join(cmd_fetch_remote))

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_dir):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_dir}")
        os.chdir(repo_dir)

        if not self.run_cmd(cmd_remote_add,
                            f"{RED}Adding new remote failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        if not self.run_cmd(cmd_fetch_remote,
                            f"{RED}New remote fetch failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)

        return True

    def sync_remote(self, branch, remote, repo_dir, dry_run=False):
        """
        Push local branch to the remote.

        Args:
            branch (str):   The source branch to be pushed
            remote (str):   The target remote for the command
            repo_dir (str): A relative directory of the repository
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If the push
                           was successful returns True, if not it returns False
        """
        cmd_push = ["git", "push", remote, branch]

        if dry_run:
            self.checkout_branch(branch, dry_run=True)
            self.logger.debug("CMD: " + " ".join(cmd_push))
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_dir):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_dir}")
        os.chdir(repo_dir)

        if not self.checkout_branch(branch):
            os.chdir(workspace_dir)
            return False

        self.logger.debug("CMD: " + " ".join(cmd_push))
        if not self.run_cmd(cmd_push,
                            f"{RED}Push to the {remote} failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)

        return True