import os
from argparse import ArgumentParser

def compare2(test_line):
    import os
    a = 1
    for root, dirs, files in os.walk("/home/mykola/repo_test/acc_test/share/here/routing/spec/international"):
        for f in files:
            fullpath = os.path.join(root, f)
            super_key = "*** Keywords ***\n"
            current_plan = ""
            points = list()
            links = dict()
            handle = open("rez.txt", "a")
            a += 1
            with open(fullpath) as _file:
                read_data = _file.readlines()
                keywords_flag = False
                links = dict()
                # print(_file)
                # handle.write(fullpath + '\n')
                for line in read_data:
                    if line == super_key:
                        keywords_flag = True
                        # handle.write(line + '\n')
                    if keywords_flag:
                        if "at(" in line and "waypoint" in line:
                            if test_line == line.split('at(')[1].split(")")[0]:
                                print("Test", test_line, line)
                                # print("Carrent",line.split('at(')[1].split(")")[0])
                                print("***THE same waypount in ", current_plan, '\n', a - 1, '\n', fullpath, '\n', line,
                                      '\n')
                                # print("        THE same waypoint in ", a - 1, fullpath, '\n', i + 1, line)
                                val_str1 = ("the same waypount in ", a - 1, fullpath)
                                val_str2 = ("______", i + 1, line)
                                handle.write(str(val_str1) + '\n')
                                handle.write(str(current_plan) + '\n')
                                handle.write(str(val_str2) + '\n')

                        if line.startswith("Provided route"):
                            if points:
                                links[current_plan] = (points[0], points[-1])
                            current_plan = line.strip()
                            # print(current_plan)
                            # handle.write(current_plan + '\n')
                            points = list()
            if points:
                links[current_plan] = (points[0], points[-1])


def lenth_file():
    """ This fanction count line in file rex.txt"""
    l7 = 0
    with open("rez.txt", "r") as ff:
        for rrr in ff:
            l7 += 1
    print(l7)
    return l7


def minus_four_line():
    ''' This fanction remove last 4 lines - when the unique points
    appears in one file only '''
    readFile = open("rez.txt")
    lines1 = readFile.readlines()
    readFile.close()
    w = open("rez.txt", 'w')
    w.writelines([item for item in lines1[:-4]])
    w.close()


# Create list D with string
a = 1
d = []
for root, dirs, files in os.walk("/home/mykola/repo_test/acc_test/share/here/routing/spec/international"):
    for f in files:
        # handle = open("output.txt", "a")
        fullpath = os.path.join(root, f)
        if os.path.splitext(fullpath)[1] == '.robot':
            a += 1
            searchfile = open(fullpath, "r")
            for i, line in enumerate(searchfile):
                if "at(" in line and "waypoint" in line:
                    d.append(line)
                i += 1
            searchfile.close()

# New list with only unique points
b = []
for lin in d:
    t = (lin.split('at(')[1].split(")")[0])
    if t not in b:
        b.append(t)

# Compare list b with all points in test
handle = open("rez.txt", "w")
handle.close()
for lin in b:
    handle = open("rez.txt", "a")
    P = "##### CHECK this waypoint for dublicate", lin, "#########################"
    print(P)
    print(sum(1 for line in open("rez.txt", "r")))
    k1 = sum(1 for line in open("rez.txt", "r"))
    handle.write(str(P) + '\n')
    handle.close()
    compare2(lin)
    k2 = sum(1 for line in open("rez.txt", "r"))
    print(sum(1 for line in open("rez.txt", "r")))
    if (k2 - k1) == 4:
        minus_four_line()

print("Count for unique points -", len(b))
print(lenth_file())
