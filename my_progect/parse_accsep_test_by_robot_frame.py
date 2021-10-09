"""
    Search_duplicate_points_in_tests_in_robot_files
"""
import os
from argparse import ArgumentParser
from robot.parsing.model import TestData




def compare_points(test_line, source, output):
    ''' This function compares the unique points
        with all points in tests'''
    counter_lines = 1
    for root, dirs, files in os.walk(source):
        for f in files:
            fullpath = os.path.join(root, f)
            super_key = "*** Keywords ***\n"
            current_plan = ""
            points = list()
            handle = open(output, "a")
            counter_lines += 1
            with open(fullpath) as _file:
                read_data = _file.readlines()
                keywords_flag = False
                links = dict()
                for line in read_data:
                    if line == super_key:
                        keywords_flag = True
                    if keywords_flag:
                        if "at(" in line and "waypoint" in line:
                            if test_line == line.split('at(')[1].split(")")[0]:
                                val_str1 = ("the same waypount in ", counter_lines - 1, fullpath)
                                val_str2 = ("______", line)
                                handle.write(str(val_str1) + '\n')
                                handle.write(str(current_plan) + '\n')
                                handle.write(str(val_str2) + '\n')
                        if line.startswith("Provided route"):
                            if points:
                                links[current_plan] = (points[0], points[-1])
                            current_plan = line.strip()
                            points = list()
            if points:
                links[current_plan] = (points[0], points[-1])


def remove_lines(output):
    ''' This function remove last 4 lines - when the unique points
    appears in one file only '''
    read_file = open(output)
    lines1 = read_file.readlines()
    read_file.close()
    w = open(output, 'w')
    w.writelines([item for item in lines1[:-4]])
    w.close()


def main():
    ''' Create list with only unique points and compare it
    with all points in all robot files   '''
    parser = ArgumentParser(description="Filter of input arguments")
    parser.add_argument("-s", "--sources", type=str, dest="sources",
                        help="Path to sources with original acceptance tests", required=True)
    parser.add_argument("-o", "--output", type=str, dest="output", help="Output folder")
    options = parser.parse_args()

    counter_lines = 1
    list_of_points = []
    for root, dirs, files in os.walk(options.sources):
        for f in files:
            fullpath = os.path.join(root, f)
            if os.path.splitext(fullpath)[1] == '.robot':
                counter_lines += 1
                searchfile = open(fullpath, "r")
                for i, line in enumerate(searchfile):
                    if "at(" in line and "waypoint" in line:
                        list_of_points.append(line)
                        print(list_of_points)
                    i += 1
                searchfile.close()

    list_of_unique_points = []
    for lin in list_of_points:
        temp1 = (lin.split('at(')[1].split(")")[0])
        if temp1 not in list_of_unique_points:
            list_of_unique_points.append(temp1)
    list_of_unique_points = (set(list_of_unique_points))

    handle = open(options.output, "w")
    handle.close()
    for lin in list_of_unique_points:
        handle = open(options.output, "a")
        prn_line = "### CHECK this waypoint for dublicate", lin, "###"
        print(prn_line)
        n_of_lines_before_comp = sum(1 for line in open(options.output, "r"))
        handle.write(str(prn_line) + '\n')
        handle.close()
        compare_points(lin, options.sources, options.output)
        n_of_lines_after_comp = sum(1 for line in open(options.output, "r"))
        if (n_of_lines_after_comp - n_of_lines_before_comp) == 4:
            remove_lines(options.output)

    print('\n', "Source folder             -", options.sources)
    print("Count of unique points     -", len(list_of_unique_points))
    print("Output folder              -", options.output)
    print("Total lines in output file -", sum(1 for line in open(options.output, "r")))


if __name__ == "__main__":
    main()
