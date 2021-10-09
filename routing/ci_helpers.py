#!/usr/bin/python
import re


def get_region_from_dvn(dvn):
    """
    Parses dvn and returns region
    """
    return re.split("(_)(\d){2,}", dvn)[0]
