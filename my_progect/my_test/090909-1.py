# A module contains tools to manipulate with partition_id.
# We will use the Partition class to get neighbour partitions.

from typing import Generator


def convert_base10_to_base4(n: int) -> str:
    if n == 0:
        return "0"
    result = ""
    while n > 0:
        result = str(n % 4) + result
        n = n // 4
    return result


def convert_base4_to_base10(n: str) -> int:
    result = 0
    for i, c in enumerate(n[::-1]):
        result += int(c) * pow(4, i)
    return result


class Partition:
    def __init__(self, partition: int) -> None:
        self.value: int = partition

    def __str__(self):
        return str(self.value)

    def parent(self) -> "Partition":
        base4 = convert_base10_to_base4(self.value)
        return Partition(convert_base4_to_base10(base4[:-1]))

    def children(self) -> Generator:
        base4 = convert_base10_to_base4(self.value)
        for i in range(4):
            yield Partition(convert_base4_to_base10("{}{}".format(base4, i)))
