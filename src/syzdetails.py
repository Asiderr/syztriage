#!/usr/bin/env python3

import logging
import pandas as pd

from io import StringIO
from src.syzcommon import SyzCommon


class SyzDetails(SyzCommon):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def _fetch_bug_report(self, url, dry_run=False) -> str:
        """
        Fetches and validates a bug report from the given URL.

        Args:
            url (str): The URL of the bug report to fetch.

        Returns:
            str: The content of the bug report.

        Raises:
            ConnectionError: If the `curl` command fails.
            ValueError: If the validation string is not found in the
            fetched report.
        """
        report_validation = '<a href="/upstream">syzbot</a>'
        cmd_dump_report = ["curl", url]
        self.logger.debug("CMD: " + " ".join(cmd_dump_report))

        if dry_run:
            return None

        if not self.run_cmd(cmd_dump_report,
                            "Fetching bug report has failed!",
                            dump_std=True):
            self.logger.error(self.stderr)
            raise ConnectionError

        if report_validation not in self.stdout:
            raise ValueError
        return self.stdout

    def _find_crashes(self, bug_html):
        """
        Extracts crash data from the provided bug report HTML.

        Args:
            bug_html (str): The HTML content of the bug report.

        Returns:
        DataFrame or None: A DataFrame containing the extracted crash data
        if the validation string is present in the HTML; otherwise, `None`.
        """
        report_validation = '<caption>Crashes'
        if report_validation not in bug_html:
            return None
        return pd.read_html(StringIO(bug_html), match="Crashes",
                            extract_links="body")[1]

    def _analyze_crashes(self, crash_table):
        """
        Analyzes and extracts valid crash information from the given crash
        table.

        Args:
            crash_table (DataFrame): A pandas DataFrame containing crash
                                     information. Expected columns include
                                     "Commit", "C repro", and "Config".

        Returns:
            list: A list of dictionaries, each containing information about
                  a valid crash.
                  Each dictionary contains the following keys:
                  - "commit" (str): The commit identifier of the crash.
                  - "config_url" (str): The URL to the configuration file.
                  - "c_repro_url" (str): The URL to the "C repro" file.
        """
        valid_crashes = []
        crash_commits = list(crash_table["Commit"])
        for i, crash_commit in enumerate(crash_commits):
            if not crash_table["C repro"][i][0]:
                continue
            config_url = ("https://syzkaller.appspot.com"
                          f"{crash_table['Config'][i][1]}")
            c_repro_url = ("https://syzkaller.appspot.com"
                           f"{crash_table['C repro'][i][1]}")
            valid_crashes.append(
                {
                    "commit": crash_commit[0],
                    "config_url": config_url,
                    "c_repro_url": c_repro_url,
                }
            )
            self.logger.debug(valid_crashes[-1])
        return valid_crashes

    def get_bug_details(self, url, dry_run=False):
        """
        Retrieves and analyzes bug details from the given URL, with error
        handling and logging.

        Args:
            url (str): The URL of the bug report to fetch and analyze.
            dry_run (bool): If flag is true method does not execute commands

        Returns:
            list or None: A list of dictionaries, each containing information
            about a valid crash, if successful. Each dictionary contains
            the following keys:
                - "commit" (str): The commit identifier of the crash.
                - "config_url" (str): The URL to the configuration file.
                - "c_repro_url" (str): The URL to the "C repro" file.
            Returns `None` if fetching or processing fails, or if no valid
            crashes are found.
        """
        if dry_run:
            self._fetch_bug_report(url, dry_run=dry_run)
            return None

        try:
            bug_html = self._fetch_bug_report(url)
            self.logger.debug(bug_html)
        except ConnectionError:
            self.logger.error("curl has failed during fetch!")
            return None
        except ValueError:
            self.logger.error("URL does not provide syzbot report!")
            return None
        crash_table = self._find_crashes(bug_html)
        if crash_table is None:
            self.logger.error("Crash table not found in the bug HTML!")
            return None
        valid_crashes = self._analyze_crashes(crash_table)
        if not valid_crashes:
            self.logger.error("No valid crashes found!")
            return None
        return valid_crashes
