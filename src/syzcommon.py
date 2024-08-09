#!/usr/bin/env python3

import logging
import subprocess
import shutil
import sys
import os

# Terminal formatting
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
ENDC = '\033[0m'

HOME_DIR = os.path.expanduser("~")
SSH_KEY = f"{HOME_DIR}/.ssh/linux-kernel-vscode-rsa"


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
                                dump_std=True):
                return False
            if self.stdout:
                self.logger.debug(self.stdout)
            else:
                return False
        except FileNotFoundError:
            self.logger.error(f"{RED}git command not available!{ENDC}")
            return False

        return True

    def clone_repository(self, repo, branch=None, dry_run=False):
        """
        Clone git repository.

        Args:
            repo (str):     A repository to be cloned
            branch (str):   A branch to be checkout
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If clone was
                           successful returns True, if not it returns False
        """
        cmd_clone = ["git", "clone", repo]
        if branch:
            cmd_clone.append("-b")
            cmd_clone.append(branch)
        self.logger.debug("CMD: " + " ".join(cmd_clone))

        if dry_run:
            return True

        # Run "git clone command"
        if not self.run_cmd(cmd_clone, f"{RED}Repository clone failed!{ENDC}"):
            return False
        return True

    def remove_repository(self, repo_path, dry_run=False):
        """
        Remove repository.

        Args:
            repo_path (str): A repository relative directory where a new remote
                            will be added
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If deleting
                           repository was successful returns True, if not it
                           returns False
        """
        if dry_run:
            return True

        if not os.path.exists(repo_path):
            self.logger.warning(f"{YELLOW}Repository doesn't exist!{ENDC}")
            return True

        shutil.rmtree(repo_path, ignore_errors=True)
        if os.path.exists(repo_path):
            self.logger.error(f"{RED}Deletion failed!{ENDC}")
            return False

        self.logger.debug(f"{repo_path} deleted successfully")
        return True

    def checkout_branch(self, repo_path, branch, dry_run=False):
        """
        Remove repository.

        Args:
            repo_path (str): A repository relative directory where a new remote
                            will be added
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If repository
                           checkout was successful returns True, if not it
                           returns False
        """
        cmd_checkout = ["git", "checkout", branch]
        err_msg = "doesn't exist in the repository."
        self.logger.debug("CMD: " + " ".join(cmd_checkout))

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not self.run_cmd(cmd_checkout,
                            f"{RED}{branch} {err_msg}!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)

        return True

    def add_repository_remote(self, repo_path, remote_uri, remote_name,
                              dry_run=False):
        """
        Check if git add new repository remote.

        Args:
            repo_path (str):    A repository relative directory where a new
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
        self.logger.debug("CMD: " + " ".join(cmd_remote_add))

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not self.run_cmd(cmd_remote_add,
                            f"{RED}Adding new remote failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)

        return True

    def fetch_repository_remote(self, repo_path, remote_name, dry_run=False):
        """
        Fetch existing repository remote.

        Args:
            repo_path (str):    A repository relative directory where a new
                               remote will be added
            remote_name (str): Name of the new remote
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            status (bool): Return status based on return code. If fetching
                           remote was successful returns True, if not it
                           returns False
        """
        cmd_fetch_remote = ["git", "fetch", remote_name]
        self.logger.debug("CMD: " + " ".join(cmd_fetch_remote))

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not self.run_cmd(cmd_fetch_remote,
                            f"{RED}New remote fetch failed!{ENDC}"):
            os.chdir(workspace_dir)
            return False

        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)

        return True

    def check_repository_remote(self, repo_path, repo_name, dry_run=False):
        """
        Checks if a remote repository with the given name exists in the
        specified local repository.

        Parameters:
        repo_path (str): The path to the local Git repository.
        repo_name (str): The name of the remote repository to check for.
        dry_run (bool): If True, simulates the check without making any changes
                        (default is False).

        Returns:
        bool: True if the remote repository exists or if dry_run is True,
              False otherwise.

        Logging:
        - Logs debug information about the commands being executed.
        - Logs an error if the repository path does not exist.
        """
        cmd_remote_list = ["git", "remote", "-v"]
        self.logger.debug("CMD: " + " ".join(cmd_remote_list))
        self.remote_name = None

        if dry_run:
            self.remote_name = "dry run"
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not self.run_cmd(cmd_remote_list,
                            f"{RED}Remote check failed!{ENDC}",
                            dump_std=True):
            os.chdir(workspace_dir)
            return False

        for line in self.stdout.splitlines():
            line_list = line.split("\t")
            if repo_name in line_list[1]:
                self.remote_name = line_list[0]
                break
        os.chdir(workspace_dir)

        if self.remote_name:
            return True
        return False

    def send_file_to_vm(self, file, dry_run=False):
        """
        Sends a file to a virtual machine using SCP (Secure Copy Protocol).

        Parameters:
        file (str): The path to the file to be sent to the VM.
        dry_run (bool): If True, simulates the file transfer without making
                        any changes (default is False).

        Returns:
        bool: True if the file transfer is successful or if dry_run is True,
              False otherwise.

        Note:
        - This method assumes `SSH_KEY` is a predefined constant representing
          the path to the SSH key file.
        """
        scp_cmd = ["scp", "-P", "5555", "-r", "-i", SSH_KEY, "-o",
                   "IdentitiesOnly=yes", "-o",
                   "NoHostAuthenticationForLocalhost=yes", file,
                   "root@localhost:/root"]
        self.logger.debug("CMD: " + " ".join(scp_cmd))

        if dry_run:
            return True

        if not os.path.exists(SSH_KEY):
            self.logger.error(f"{RED}SSH key doesn't exist!{ENDC}")
            return False

        if not os.path.exists(file):
            self.logger.error(f"{RED}{file} doesn't exist!{ENDC}")
            return False

        if not self.run_cmd(scp_cmd,
                            f"{RED}Copying {file} file to vm failed!{ENDC}"):
            return False
        return True

    def run_vm_command(self, vm_cmd, dry_run=False):
        """
        Runs a specified command on a virtual machine via SSH.

        Parameters:
        vm_cmd (list): The command to run on the VM, provided as a list of
                       command arguments.
        dry_run (bool): If True, simulates running the command without making
                        any changes (default is False).

        Returns:
        bool: True if the command is successfully executed or if dry_run
              is True, False otherwise.

        Note:
        - This method assumes `SSH_KEY` is a predefined constant representing
          the path to the SSH key file.
        """
        ssh_cmd = ["ssh", "-p", "5555", "-i", SSH_KEY, "-o",
                   "IdentitiesOnly=yes", "-o",
                   "NoHostAuthenticationForLocalhost=yes",
                   "root@localhost"] + vm_cmd
        self.logger.debug("CMD: " + " ".join(ssh_cmd))

        if dry_run:
            return True

        if not os.path.exists(SSH_KEY):
            self.logger.error(f"{RED}SSH key doesn't exist!{ENDC}")
            return False

        if not self.run_cmd(ssh_cmd,
                            f"{RED}Running ssh cmd failed!{ENDC}"):
            return False
        return True
