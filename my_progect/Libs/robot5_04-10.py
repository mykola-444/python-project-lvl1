import os

for root, dirs, files in os.walk("/home/mykola/Videos"):
    for f in files:
        fullpath = os.path.join(root, f)
        super_key = "*** Keywords ***\n"
        current_plan = ""
        points = list()
        links = dict()
        dic_p = {}
        with open(fullpath) as _file:
            read_data = _file.readlines()
            keywords_flag = False
            links = dict()
            print(_file)
            for line in read_data:
                if line == super_key:
                    keywords_flag = True
                    print(line)
                if keywords_flag:
                    if "at(" in line and "waypoint" in line:
                        print(line)
                        # print([x.strip() for x in line[line.find("at(") + 3:-2].split(",")])

                        points.append([x.strip() for x in line[line.find("at(") +
                                                               3:-2].split(",")])

                    if line.startswith("Provided route"):
                        if points:
                            links[current_plan] = (points[0], points[-1])
                        current_plan = line.strip()
                        print(current_plan)

                        points = list()
                        dic_p[current_plan] = points

        if points:
            links[current_plan] = (points[0], points[-1])

for x, y in dic_p.items():
    print(x, y)

# def compare1(coord, file1, current_plan1, point1):
#     import os
#     a = 1
#     for root, dirs, files in os.walk("/home/mykola/acc_test/share/here/routing/spec/international/bicycle"):
#         for f in files:
#             #handle = open("output.txt", "a")
#             fullpath = os.path.join(root, f)
#             if os.path.splitext(fullpath)[1] == '.robot':
#                 #print(a, fullpath)
#                 a = a + 1
#                 #handle.write(fullpath + '\n')
#                 searchfile = open(fullpath, "r")
#                 for i, line in enumerate(searchfile):
#                     if "at(" in line and "waypoint" in line:
#                         if test_line == line.split('at(')[1].split(")")[0]:
#                             print("***THE same waypount in ", a-1, fullpath, '\n', i+1, line)
#
#                     i += 1
#                 searchfile.close()

#

#
