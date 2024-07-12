#!/usr/bin/env python3

import logging
import itertools
import os
import subprocess
import sys
import time

from src.syzcommon import SyzCommon, SSH_KEY

# Terminal formatting
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
ENDC = '\033[0m'

HOME_DIR = os.path.expanduser("~")
IMAGE_PATH = f"{HOME_DIR}/.linux-kernel-vscode/debian-x86_64.img"


class SyzReproduce(SyzCommon):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def _run_vm(self, repo_path, dry_run=False):
        """
        Runs a virtual machine (VM) using QEMU with specified configurations.

        Parameters:
        repo_path (str): The path to the repository containing the kernel
                         image.
        dry_run (bool): If True, simulates running the VM without making any
                        changes (default is False).

        Returns:
        bool: True if the VM starts successfully or if dry_run is True,
              False otherwise.

        Raises:
        TimeoutError: If the VM startup exceeds the specified timeout.

        Note:
        - This method assumes `IMAGE_PATH` is a predefined constant
          representing the path to the VM image.
        """
        kernel_path = f"{repo_path}/arch/x86_64/boot/bzImage"
        cmd_run_qemu_vm = ["qemu-system-x86_64", "-enable-kvm", "-cpu", "host",
                           "-machine", "q35", "-bios", "qboot.rom", "-s",
                           "-nographic", "-smp", "4", "-m", "8G", "-qmp",
                           "tcp:localhost:4444,server,nowait",
                           "-serial", "mon:stdio", "-net",
                           "nic,model=virtio-net-pci", "-net",
                           "user,hostfwd=tcp::5555-:22", "-virtfs",
                           ("local,path=/,mount_tag=hostfs,"
                            "security_model=none,multidevs=remap"),
                           "-append", ('console=ttyS0,115200 '
                                       'root=/dev/sda rw nokaslr '
                                       'init=/lib/systemd/systemd '
                                       'debug systemd.log_level=info'),
                           "-drive",
                           f"file={IMAGE_PATH},format=raw",
                           "-kernel", kernel_path]
        self.logger.debug("CMD: " + " ".join(cmd_run_qemu_vm))
        spinner = itertools.cycle(['-', '/', '|', '\\'])
        vm_timeout = 600
        self.vm = None

        if dry_run:
            return True

        workspace_dir = os.getcwd()
        if not os.path.exists(repo_path):
            self.logger.error(f"{RED}Repository doesn't exist!{ENDC}")
            return False

        self.logger.debug(f"CMD: cd {repo_path}")
        os.chdir(repo_path)

        if not os.path.exists(kernel_path):
            self.logger.error(f"{RED}Kernel does not exist!{ENDC}")
            os.chdir(workspace_dir)
            return False

        p = subprocess.Popen(
            cmd_run_qemu_vm,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        time_now = time.time()
        self.logger.info("Starting VM...")
        while "root@debian-vm:~$" not in p.stdout.readline().decode("utf-8"):
            if (time.time() - time_now) > vm_timeout:
                self.logger.error(f"{RED}The VM startup has exceeded the"
                                  f" time limit!{ENDC}")
                p.kill()
                os.chdir(workspace_dir)
                raise TimeoutError
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            sys.stdout.write('\b')

        self.vm = p
        self.logger.debug(f"CMD: cd {workspace_dir}")
        os.chdir(workspace_dir)
        return True

    def _build_c_repro(self, c_repro_uri, dry_run=False):
        """
        Downloads and builds a C reproducer from a given URI.

        Parameters:
        c_repro_uri (str): The URI of the C reproducer source file to download.
        dry_run (bool): If True, simulates the download and build process
                        without making any changes (default is False).

        Returns:
        bool: True if the download and build processes are successful or if
              dry_run is True, False otherwise.
        """
        cmd_download_repro = ["curl", c_repro_uri, "-o", "/tmp/syzbot-repro.c"]
        cmd_build_repro = ["clang", "-static", "-lpthread",
                           "/tmp/syzbot-repro.c", "-o", "/tmp/syzbot-repro"]
        self.logger.debug("CMD: " + " ".join(cmd_download_repro))
        self.logger.debug("CMD: " + " ".join(cmd_build_repro))

        if dry_run:
            return True

        if not self.run_cmd(cmd_download_repro,
                            f"{RED}Downloading C repro source failed!{ENDC}"):
            return False

        if not os.path.exists("/tmp/syzbot-repro.c"):
            self.logger.error(f"{RED}C reproducer source not found!{ENDC}")
            return False

        if not self.run_cmd(cmd_build_repro,
                            f"{RED}Building C reproducer failed!{ENDC}"):
            return False
        return True

    def _build_internal_c_repro(self, c_repro_uri, dry_run=False):
        """
        Builds a C reproducer from an internal source file.

        Parameters:
        c_repro_uri (str): The URI or path of the internal C reproducer source
                           file to build.
        dry_run (bool): If True, simulates the build process without making any
                        changes (default is False).

        Returns:
        bool: True if the build process is successful or if dry_run is True,
              False otherwise.
        """
        cmd_build_repro = ["clang", "-static", "-lpthread",
                           f"{c_repro_uri}", "-o", "/tmp/syzbot-repro"]
        self.logger.debug("CMD: " + " ".join(cmd_build_repro))

        if dry_run:
            return True

        if not os.path.exists(c_repro_uri):
            self.logger.error(f"{RED}C reproducer source not found!{ENDC}")
            return False

        if not self.run_cmd(cmd_build_repro,
                            f"{RED}Building C reproducer failed!{ENDC}"):
            return False
        return True

    def _push_c_repro(self, dry_run=False):
        """
        Pushes a compiled C reproducer to a virtual machine.

        Parameters:
        dry_run (bool): If True, simulates the push process without making any
                        changes (default is False).

        Returns:
        bool: True if the C reproducer is successfully pushed to the VM or if
              dry_run is True, False otherwise.
        """
        c_repro = "/tmp/syzbot-repro"
        if self.vm is None and not dry_run:
            self.logger.error(f"{RED}Qemu VM is not running!{ENDC}")
            return False

        if not self.run_vm_command(["rm", "-rf", "/root/*"],
                                   dry_run=dry_run):
            self.logger.error(f"{RED}Cleaning vm workspace failed!{ENDC}")
            return False

        if not self.send_file_to_vm(c_repro, dry_run=dry_run):
            self.logger.error(f"{RED}Sending C reproducer failed!{ENDC}")
            return False
        return True

    def _run_c_repro(self, dry_run=False):
        """
        Runs a compiled C reproducer on the virtual machine (VM) via SSH.

        Parameters:
        dry_run (bool): If True, simulates running the C reproducer without
                        making any changes (default is False).

        Returns:
        str or None: The standard output of the C reproducer if successful,
                     "Dry run" if in dry_run mode, or None if the VM is
                     not running.
        """
        spinner = itertools.cycle(['-', '/', '|', '\\'])
        repro_timeout = 30
        ssh_cmd = ["ssh", "-p", "5555", "-i", SSH_KEY, "-o",
                   "IdentitiesOnly=yes", "-o",
                   "NoHostAuthenticationForLocalhost=yes",
                   "root@localhost", "./syzbot-repro"]
        self.logger.debug("CMD: " + " ".join(ssh_cmd))

        if dry_run:
            return "Dry run"

        if self.vm is None:
            self.logger.error(f"{RED}Qemu VM is not running!{ENDC}")
            return None

        time_now = time.time()
        self.logger.info("Starting C reproducer...")

        p_repro = subprocess.Popen(
            ssh_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        while not p_repro.poll():
            if (time.time() - time_now) > repro_timeout:
                self.logger.info("The C reproducer has exceeded the"
                                 " time limit.")
                self.vm.kill()
                return self.vm.stdout.read().decode("utf-8")
            sys.stdout.write(next(spinner))
            sys.stdout.flush()
            sys.stdout.write('\b')

        self.vm.kill()
        self.logger.info(f"The C reproducer returned with {p_repro.returncode}"
                         " code.")
        return self.vm.stdout.read().decode("utf-8")

    def reproduce_issue(self, crash_dict: dict, repo_path, dry_run=False,
                        internal=False):
        """
        Attempts to reproduce a given issue on a virtual machine (VM) using a
        C reproducer.

        Parameters:
        crash_dict (dict): A dictionary containing details of the crash,
                           including the key "c_repro_uri" which points to
                           the URI or path of the C reproducer source file.
        repo_path (str): The path to the repository containing the kernel and
                         related files.
        dry_run (bool): If True, simulates the entire process without making
                        any changes (default is False).
        internal (bool): If True, uses internal methods to build the C
                         reproducer (default is False).

        Returns:
        tuple: A tuple containing:
            - bool: True if the issue is reproduced successfully or if
                    dry_run is True, False otherwise.
            - str: A string message indicating the status, which can be
                   "Dry run", "Valid", "Err", or "Invalid".
        """
        self.vm_stdout = None

        try:
            self._run_vm(repo_path, dry_run=dry_run)
        except TimeoutError:
            return False, "Err"

        if self.vm is None and not dry_run:
            self.logger.error(f"{RED}Failed to run vm!{ENDC}")
            return False, "Err"

        if not internal or not self._build_internal_c_repro(
            crash_dict["c_repro_uri"],
            dry_run=dry_run
        ):
            self.logger.error(f"{RED}Failed to build internal C "
                              f"reproducer!{ENDC}")
            self.vm.kill()
            return False, "Err"

        if not (internal or self._build_c_repro(crash_dict["c_repro_uri"],
                                                dry_run=dry_run)):
            self.logger.error(f"{RED}Failed to build C reproducer!{ENDC}")
            self.vm.kill()
            return False, "Err"

        if not self._push_c_repro(dry_run=dry_run):
            self.logger.error(f"{RED}Failed to push C reproducer to vm!{ENDC}")
            self.vm.kill()
            return False, "Err"

        self.vm_stdout = self._run_c_repro(dry_run=dry_run)
        if not self.vm_stdout:
            self.logger.error(f"{RED}Failed to run C reproducer!{ENDC}")
            return False, "Err"

        if "Dry run" in self.vm_stdout:
            return True, "Dry run"

        self.logger.debug(self.vm_stdout)
        if "Rebooting in" in self.vm_stdout:
            return True, "Valid"
        return False, "Invalid"
