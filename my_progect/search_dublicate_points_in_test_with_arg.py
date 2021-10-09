import os
from argparse import ArgumentParser
from robot.parsing.model import TestData


#Create list D with string
counter_lines = 1
list_of_points = []
for root, dirs, files in os.walk('/home/mykola/repo_test/acc_test/share/here/routing/spec/international/truck'):
    for f in files:
        fullpath = os.path.join(root, f)
        super_key = "*** Keywords ***\n"
        print(fullpath)
        if os.path.splitext(fullpath)[1] == '.robot':
            counter_lines += 1
            searchfile = open(fullpath, "r")
            print(fullpath)
            suite = TestData(source=fullpath)
            for test_case in suite.keyword_table:
                print(test_case.name)
            # for i, line in enumerate(searchfile):
            #     if "at(" in line and "waypoint" in line:
            #         print(line)
            #         list_of_points.append(line)
            #    i += 1
            searchfile.close()





































#
# def compare2(test_line):
#     ''' This function compares the unique points
#         with all points in tests'''
#     a = 1
#     for root, dirs, files in os.walk(options.sources):
#         for f in files:
#             fullpath = os.path.join(root, f)
#             super_key = "*** Keywords ***\n"
#             current_plan = ""
#             points = list()
#             handle = open(options.output, "a")
#             a += 1
#             with open(fullpath) as _file:
#                 read_data = _file.readlines()
#                 keywords_flag = False
#                 links = dict()
#                 for line in read_data:
#                     if line == super_key:
#                         keywords_flag = True
#                     if keywords_flag:
#                         if "at(" in line and "waypoint" in line:
#                             if test_line == line.split('at(')[1].split(")")[0]:
#                                 print("Test",test_line, line)
#                                 print("***THE same waypount in ", current_plan, '\n', a - 1, '\n', fullpath, '\n', line,
#                                       '\n')
#                                 val_str1 = ("the same waypount in ", a - 1, fullpath)
#                                 val_str2 = ("______", line)
#                                 handle.write(str(val_str1) + '\n')
#                                 handle.write(str(current_plan) + '\n')
#                                 handle.write(str(val_str2) + '\n')
#
#                         if line.startswith("Provided route"):
#                             if points:
#                                 links[current_plan] = (points[0], points[-1])
#                             current_plan = line.strip()
#                             points = list()
#             if points:
#                 links[current_plan] = (points[0], points[-1])
#
#
# def lenth_file():
#     """ This fanction count line in file rex.txt"""
#     l7 = 0
#     with open(options.output, "r") as ff:
#         for rrr in ff:
#             l7 += 1
#     print(l7)
#     return l7
#
#
# def minus_four_line():
#     ''' This fanction remove last 4 lines - when the unique points
#     appears in one file only '''
#     readFile = open(options.output)
#     lines1 = readFile.readlines()
#     readFile.close()
#     w = open(options.output, 'w')
#     w.writelines([item for item in lines1[:-4]])
#     w.close()
#
#
# parser = ArgumentParser(description="Filter partitions ids.")
# parser.add_argument("-s", "--sources", type=str, dest="sources",
#                         help="Path to sources with original acceptance tests", required=True)
# parser.add_argument("-o", "--output", type=str, dest="output", help="Output folder")
# options = parser.parse_args()
#
#
# # Create list D with string
# a = 1
# d = []
# for root, dirs, files in os.walk(options.sources):
#     for f in files:
#         fullpath = os.path.join(root, f)
#         if os.path.splitext(fullpath)[1] == '.robot':
#             a += 1
#             searchfile = open(fullpath, "r")
#             for i, line in enumerate(searchfile):
#                 if "at(" in line and "waypoint" in line:
#                     d.append(line)
#                 i += 1
#             searchfile.close()
#
# # New list with only unique points
# b = []
# for lin in d:
#     t = (lin.split('at(')[1].split(")")[0])
#     if t not in b:
#         b.append(t)
#
# # Compare list b with all points in test
# handle = open(options.output, "w")
# handle.close()
# for lin in b:
#     handle = open(options.output, "a")
#     P = "##### CHECK this waypoint for dublicate", lin, "#########################"
#     print(P)
#     print(sum(1 for line in open(options.output, "r")))
#     k1 = sum(1 for line in open(options.output, "r"))
#     handle.write(str(P) + '\n')
#     handle.close()
#     compare2(lin)
#     k2 = sum(1 for line in open(options.output, "r"))
#     print(sum(1 for line in open(options.output, "r")))
#     if (k2 - k1) == 4:
#         minus_four_line()
#
# print("Count for unique points -", len(b))
# print(lenth_file())
#
#
# def main():
#     parser = ArgumentParser(description="Filter partitions ids.")
#     parser.add_argument("-s", "--sources", type=str, dest="sources",
#                         help="Path to sources with original acceptance tests", required=True)
#     parser.add_argument("-o", "--output", type=str, dest="output", help="Output folder")
#     options = parser.parse_args()
#
#
#
# if __name__ == "__main__":
#     main()

