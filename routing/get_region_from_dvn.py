import sys
from ci_helpers import get_region_from_dvn


if __name__ == "__main__":
    print(get_region_from_dvn(sys.argv[1]))
