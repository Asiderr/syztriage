#!/usr/bin/env python3
import argparse
import logging
import time

from src.syzdetails import SyzDetails
from src.syzsetup import SyzSetup
from src.syzreproduce import SyzReproduce
from src.syzinternal import SyzInternal

# Terminal formatting
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
ENDC = '\033[0m'

BUGS_LIST = [
    "https://syzkaller.appspot.com/bug?extid=824b138c39c77ad6775f",
]
LINUX_REPO_PATH = "/home/nkaminski/data/infogain/linux"


class SyzTriage(SyzDetails, SyzSetup, SyzReproduce, SyzInternal):
    def __init__(self) -> None:
        self._cmdline_parser()
        self._args = self.args_parser.parse_args()
        self.verbose = self._args.verbose or self._args.dry_run
        self.dry_run = self._args.dry_run
        self.internal_bugs = self._args.internal_bugs
        self._logger_setup(verbose=self.verbose)

    def _logger_setup(self, verbose=False):
        """
        Create logger based on the verbosity level.

        Args:
            verbose (bool): If True, set the logging level to DEBUG; otherwise
            set it to INFO.

        Returns:
            self.log (logger): logger handler
        """
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger(__name__)

    def _cmdline_parser(self):
        """
        Create command line parameters parser.

        Returns:
            self.args (logger): parser handler
        """
        parser = argparse.ArgumentParser(
            description="Triaging tool for Syzkernel bugs."
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Increase logs verbosity level"
        )
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="Do not execute commands."
        )
        parser.add_argument(
            "-i",
            "--internal-bugs",
            action="store_true",
            help="Triage internal bugs."
        )
        self.args_parser = parser

    def triage_internal_syzkaller_bugs(self, dry_run=False):
        """
        Triage internal Syzkaller bugs by reproducing them in a Linux
        kernel environment.

        Parameters:
        dry_run (bool): If True, simulates the entire triage process without
                        making any changes (default is False).

        Returns:
        bool: True if all bugs were triaged successfully or if dry_run is
              True and no actual triage is performed, False otherwise.
        """
        bugs_reproduced = []
        bugs_not_reproduced = []
        bugs_error = []
        status = False
        log_file_name = f"syztriage-{int(time.time())}.log"
        with open(log_file_name, "a+") as f:
            self.logger.info("Getting internal bug details.")
            valid_crashes = self.get_internal_bug_details(dry_run=dry_run)
            if not valid_crashes:
                self.logger.error(f"{RED}Getting bug details failed!"
                                  f"{ENDC}")
                return False
            for crash_dict in valid_crashes:
                self.logger.info("Setting up Linux repository.")
                if not self.setup_kernel_repository(crash_dict,
                                                    LINUX_REPO_PATH,
                                                    dry_run=dry_run):
                    self.logger.error(f"{RED}Setting up Linux repository "
                                      f"failed!{ENDC}")
                    bugs_error.append(crash_dict["task_name"])
                    continue
                self.logger.info("Reproducing bug.")
                status, cause = self.reproduce_issue(crash_dict,
                                                     LINUX_REPO_PATH,
                                                     dry_run=dry_run,
                                                     internal=True)
                f.writelines("================================================"
                             "===========================================\r\n")
                f.writelines(f"{crash_dict['task_name']}\r\n")
                f.writelines("================================================"
                             "===========================================\r\n")
                if self.vm_stdout:
                    f.write(self.vm_stdout)

                if status and cause == "Valid":
                    bugs_reproduced.append(crash_dict["task_name"])
                    continue
                elif status and cause == "Dry run":
                    bugs_not_reproduced.append(crash_dict["task_name"])
                    continue
                elif cause == "Err":
                    self.logger.error(f"{RED}Error during bug reproduction!"
                                      f"{ENDC}")
                    bugs_error.append(crash_dict["task_name"])
                elif cause == "Invalid":
                    bugs_not_reproduced.append(crash_dict["task_name"])
                    continue
                else:
                    self.logger.error(f"{RED}Error during bug reproduction!"
                                      f"{ENDC}")
                    bugs_error.append(crash_dict["task_name"])

        if not bugs_error and not bugs_not_reproduced and not bugs_reproduced:
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            self.logger.error(f"{RED}No bugs were processed!{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            return status

        if not bugs_error:
            status = True
        else:
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            self.logger.error(f"{RED}{BOLD}Some errors happened"
                              f" during reproduction of the bugs!{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            for i, bug in enumerate(bugs_error):
                self.logger.error(f"{RED}{BOLD}{i+1}. {bug}{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")

        if bugs_not_reproduced:
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")
            self.logger.info(f"{BLUE}{BOLD}Some bugs were not "
                             f"reproduced.{ENDC}")
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")
            for i, bug in enumerate(bugs_not_reproduced):
                self.logger.info(f"{BLUE}{i+1}. {bug}{ENDC}")
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")

        if bugs_reproduced:
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}Some bugs were reproduced.{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
            for i, bug in enumerate(bugs_reproduced):
                self.logger.info(f"{GREEN}{i+1}. {bug}{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
        return status

    def triage_syzkaller_bugs(self, dry_run=False):
        """
        Triage Syzkaller bugs by reproducing them in a Linux kernel
        environment.

        Parameters:
        dry_run (bool): If True, simulates the entire triage process without
                        making any changes (default is False).

        Returns:
        bool: True if all bugs were triaged successfully or if dry_run is
              True and no actual triage is performed, False otherwise.
        """
        bugs_reproduced = []
        bugs_not_reproduced = []
        bugs_error = []
        status = False
        log_file_name = f"syztriage-{int(time.time())}.log"
        with open(log_file_name, "a+") as f:
            for bug in BUGS_LIST:
                self.logger.info(f"Processing bug: {bug}")
                self.logger.info("Getting bug details.")
                valid_crashes = self.get_bug_details(bug, dry_run=dry_run)
                if not valid_crashes:
                    self.logger.error(f"{RED}Getting bug details failed!"
                                      f"{ENDC}")
                    bugs_error.append(bug)
                    continue
                crash_dict = valid_crashes[0]
                self.logger.info("Setting up Linux repository.")
                if not self.setup_kernel_repository(crash_dict,
                                                    LINUX_REPO_PATH,
                                                    dry_run=dry_run):
                    self.logger.error(f"{RED}Setting up Linux repository "
                                      f"failed!{ENDC}")
                    bugs_error.append(bug)
                    continue
                self.logger.info("Reproducing bug.")
                status, cause = self.reproduce_issue(crash_dict,
                                                     LINUX_REPO_PATH,
                                                     dry_run=dry_run)
                f.writelines("================================================"
                             "===========================================\r\n")
                f.writelines(f"{bug}\r\n")
                f.writelines("================================================"
                             "===========================================\r\n")
                if self.vm_stdout:
                    f.write(self.vm_stdout)

                if status and cause == "Valid":
                    bugs_reproduced.append(bug)
                    continue
                elif status and cause == "Dry run":
                    bugs_not_reproduced.append(bug)
                    continue
                elif cause == "Err":
                    self.logger.error(f"{RED}Error during bug reproduction!"
                                      f"{ENDC}")
                    bugs_error.append(bug)
                elif cause == "Invalid":
                    bugs_not_reproduced.append(bug)
                    continue
                else:
                    self.logger.error(f"{RED}Error during bug reproduction!"
                                      f"{ENDC}")
                    bugs_error.append(bug)

        if not bugs_error and not bugs_not_reproduced and not bugs_reproduced:
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            self.logger.error(f"{RED}No bugs were processed!{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            return status

        if not bugs_error:
            status = True
        else:
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            self.logger.error(f"{RED}{BOLD}Some errors happened"
                              f" during reproduction of the bugs!{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")
            for i, bug in enumerate(bugs_error):
                self.logger.error(f"{RED}{BOLD}{i+1}. {bug}{ENDC}")
            self.logger.error(f"{RED}{BOLD}=============================="
                              f"====================================={ENDC}")

        if bugs_not_reproduced:
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")
            self.logger.info(f"{BLUE}{BOLD}Some bugs were not "
                             f"reproduced.{ENDC}")
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")
            for i, bug in enumerate(bugs_not_reproduced):
                self.logger.info(f"{BLUE}{i+1}. {bug}{ENDC}")
            self.logger.info(f"{BLUE}{BOLD}=============================="
                             f"======================================={ENDC}")

        if bugs_reproduced:
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}Some bugs were reproduced.{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
            for i, bug in enumerate(bugs_reproduced):
                self.logger.info(f"{GREEN}{i+1}. {bug}{ENDC}")
            self.logger.info(f"{GREEN}{BOLD}=============================="
                             f"========================================{ENDC}")
        return status


if __name__ == "__main__":
    syz = SyzTriage()
    if syz.internal_bugs:
        status = syz.triage_internal_syzkaller_bugs(dry_run=syz.dry_run)
    else:
        status = syz.triage_syzkaller_bugs(dry_run=syz.dry_run)

    if status:
        exit(0)
    else:
        exit(1)
