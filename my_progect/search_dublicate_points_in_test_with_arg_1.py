import os
from argparse import ArgumentParser
from robot.parsing.model import TestData


def check_for_test_case(test_file_pass):
    with open(test_file_pass) as _file:
        super_key = "*** Keywords ***\n"
        read_data = _file.readlines()
        keywords_flag = False
        for line in read_data:
            if line == super_key:
                keywords_flag = True
    return keywords_flag





#Create list D with string
counter_lines = 1
list_of_points = []
for root, dirs, files in os.walk('/home/mykola/repo_test/acc_test/share/here/routing/spec/international/truck/'):
    for f in files:
        fullpath = os.path.join(root, f)
        #print(fullpath)
        if os.path.splitext(fullpath)[1] == '.robot' and check_for_test_case(fullpath):
            counter_lines += 1
            searchfile = open(fullpath, "r")
            print(fullpath)
            suite = TestData(source=fullpath)
            for test_case in suite.keyword_table:
                 print(test_case.name)
                 if "at(" in line and "waypoint" in line:
                   #         print(line)
                   #

            # suite = TestData(source=fullpath)
            # for test_case in suite.keyword_table:
            #     if "at(" in line and "waypoint" in line:
            #         print(test_case.name)
            # for i, line in enumerate(searchfile):
            #     if "at(" in line and "waypoint" in line:
            #         print(line)
            #         list_of_points.append(line)
            #    i += 1
            searchfile.close()












