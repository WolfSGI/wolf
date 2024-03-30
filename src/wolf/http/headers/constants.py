import re
from enum import Enum

WEIGHT = re.compile(r"^(0\.[0-9]{1,3}|1\.0{1,3})$")  # 3 decimals.
WEIGHT_PARAM = re.compile(r"^q=(0\.[0-9]{1,3}|1\.0{1,3})$")


class Specificity(int, Enum):
    NONSPECIFIC = 0
    PARTIALLY_SPECIFIC = 1
    SPECIFIC = 2
