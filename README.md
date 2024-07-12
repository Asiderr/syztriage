# syztriage

A syzkaller error automation tool that aims to speed up the triage process.

## Global parameters

### SSH_KEY for vm ([syzcommon.py](src/syzcommon.py))

Key used to communicate with qemu vm where the bug is reproduced

```py
SSH_KEY = f"{HOME_DIR}/.ssh/linux-kernel-vscode-rsa"
```

### INTERNAL_BUGS ([syzinternal.py](src/syzinternal.py))

List of internal bugs to be triaged.

```py
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
```

### INTERNAL_BUGS ([syzinternal.py](src/syzinternal.py))

Kernel config used during internal trianging.

```py
INTERNAL_CONFIG = ("https://syzkaller.appspot.com/text?tag=KernelConfig&x="
                   "c3820d4fff43c7a3")
```

### IMAGE_PATH

Absolute path to the VM image.

```py
IMAGE_PATH = f"{HOME_DIR}/.linux-kernel-vscode/debian-x86_64.img"
```

### BUGS_LIST ([syztriage.py](src/syztriage.py))

List of bugs reproduced from the syzkaller reports.

```py
BUGS_LIST = [
    "https://syzkaller.appspot.com/bug?extid=824b138c39c77ad6775f",
]
```

## Usage


Clone syztriage repository

```sh
$ git clone git@github.com:Asiderr/syztriage.git
```

Change directory to the cloned repo and set global variables as it is described
above.


### Triaging bugs reproduced from the syzkaller reports

```sh
$ python -m src.syztriage
```

### Triaging internal bugs

```sh
$ python -m src.syztriage -i
```

### Help message

```sh
$ python3 -m src.syztriage -h
usage: syztriage.py [-h] [-v] [-d] [-i]

Triaging tool for Syzkernel bugs.

options:
  -h, --help           show this help message and exit
  -v, --verbose        Increase logs verbosity level
  -d, --dry-run        Do not execute commands.
  -i, --internal-bugs  Triage internal bugs
```

## Testing

To run the tests run following command:
```sh
$ python3 -m tests.test_syzdetails
....2024-07-12 15:18:00 - ERROR - Fetching bug report has failed!
2024-07-12 15:18:00 - ERROR - curl: (3) URL using bad/illegal format or missing URL

....2024-07-12 15:18:03 - ERROR - Fetching bug report has failed!
2024-07-12 15:18:03 - ERROR -   % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0curl: (6) Could not resolve host: INVALID

2024-07-12 15:18:03 - ERROR - curl has failed during fetch!
...2024-07-12 15:18:05 - ERROR - URL does not provide syzbot report!
.2024-07-12 15:18:07 - ERROR - Crash table not found in the bug HTML!
.2024-07-12 15:18:08 - ERROR - No valid crashes found!
.
----------------------------------------------------------------------
Ran 14 tests in 11.343s

OK
```
