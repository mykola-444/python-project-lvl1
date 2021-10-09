import os

from robot.parsing.model import TestData


fullpath = '/home/mykola/repo_test/acc_test/share/here/routing/spec/international/truck/__init__.robot'

super_key = "*** Keywords ***\n"

if super_key:
    print("stop")

print("contin")

suite = TestData(parent=None,
                 source=fullpath)


for f1 in suite.testcase_table:
    print(f1.name)

for test_case in suite.keyword_table:
    print(test_case.name)

for test in suite.keywords:
    print("7hgsfkgaksg", test.name)

