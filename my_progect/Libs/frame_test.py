def compare1(test_line,fullpath1,current_plan1):
    import os
    a=1
    for root, dirs, files in os.walk("/home/mykola/Videos"):
        for f in files:
            fullpath = os.path.join(root, f)
            super_key = "*** Keywords ***\n"
            current_plan = ""
            points = list()
            links = dict()
            handle = open("rez.txt", "a")
            a+=1
            with open(fullpath) as _file:
                read_data = _file.readlines()
                keywords_flag = False
                links = dict()
                #print(_file)
                handle.write(fullpath + '\n')
                for line in read_data:
                    if line == super_key:
                        keywords_flag = True
                        #handle.write(line + '\n')

                    if keywords_flag:
                        if "at(" in line and "waypoint" in line:
                            if test_line == line:
                                if fullpath != fullpath1:
                                    handle.write("syhdauydusayduyas")
                                    #print("Test",test_line)
                                    #print("Carrent",line.split('at(')[1].split(")")[0])
                                    print("***THE same waypount in ",current_plan1, '\n', a - 1, fullpath1, '\n', fullpath, '\n',   line,'\n')
                                    val_str1 = ("_______the same waypount in ", a - 1, fullpath)
                                    val_str2 = ("_______", line)
                                    print(str(val_str1), str(val_str2))
                                    handle.write("syhdauydusayduyas")
                                    handle.write(str(val_str1) + '\n')
                                    handle.write(str(val_str2) + '\n')


                            # print([x.strip() for x in line[line.find("at(") +
                            #                                3:-2].split(",")])
                            # st = ([x.strip() for x in line[line.find("at(") +
                            #                                3:-2].split(",")])
                            # st1 = str(st)
                            # handle.write(st1 + '\n')
                            # points.append([x.strip() for x in line[line.find("at(") +
                            #                                        3:-2].split(",")])

                        if line.startswith("Provided route"):
                            if points:
                                links[current_plan] = (points[0], points[-1])
                            current_plan = line.strip()
                            #print(current_plan)
                            #handle.write(current_plan + '\n')
                            points = list()
            if points:
                links[current_plan] = (points[0], points[-1])





import os
a=1
d=[]
for root, dirs, files in os.walk("/home/mykola/Videos"):
    for f in files:
        fullpath = os.path.join(root, f)
        super_key = "*** Keywords ***\n"
        current_plan = ""
        points = list()
        links = dict()
        handle = open("rez.txt", "w")
        with open(fullpath) as _file:
            read_data = _file.readlines()
            keywords_flag = False
            links = dict()
            #print(fullpath)
            #handle.write(fullpath +'\n')
            for line in read_data:
                if line == super_key:
                    keywords_flag = True
                    #print(line)
                    #handle.write(line + '\n')
                if keywords_flag:
                    if "at(" in line and "waypoint" in line:
                        #compare1(line,fullpath,current_plan)
                        #print([x.strip() for x in line[line.find("at(") + 3:-2].split(",")])
                        st=([x.strip() for x in line[line.find("at(") + 3:-2].split(",")])
                        #print(st)
                        st1=str(st)
                        #handle.write(st1+'\n')
                        points.append([x.strip() for x in line[line.find("at(") + 3:-2].split(",")])
                        #print("Main link", points[0], points[-1])
                        compare1(line, fullpath, current_plan)

                        
                    if line.startswith("Provided route"):
                        if points:
                            links[current_plan] = (points[0], points[-1])
                        current_plan = line.strip()
                        #print("Main",current_plan)

                        #handle.write(current_plan + '\n')
                        points = list()

        if points:
            links[current_plan] = (points[0], points[-1])
























# def compare1(test_line):
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
#                     if "at(" in line:
#                         if test_line == line.split('at(')[1].split(")")[0]:
#                             print("***THE same waypount in ", a-1, fullpath, '\n', i+1, line)
#                             val_str1 = ("_______the same waypount in ", a - 1, fullpath)
#                             val_str2 = ("_______",i + 1, line)
#                             s1=str(val_str1)
#                             s2=str(val_str2)
#                             handle.write(s1+'\n')
#                             handle.write(s2+'\n')
#                     i += 1
#                 searchfile.close()

#Create list D with string
# a=1
# d=[]
# for root, dirs, files in os.walk("/home/mykola/acc_test/share/here/routing/spec/international/bicycle"):
#     for f in files:
#         #handle = open("output.txt", "a")
#         fullpath = os.path.join(root, f)
#         if os.path.splitext(fullpath)[1] == '.robot':
#             a=a+1
#             searchfile = open(fullpath, "r")
#             for i, line in enumerate(searchfile):
#                 if "at(" in line:
#                     d.append(line)
#                 i+=1
#             searchfile.close()
#
# #New list with only points
# b = []
# for lin in d:
#     t = (lin.split('at(')[1].split(")")[0])
#     if t not in b:
#         b.append(t)
#
# # Cjmpare list b with all points
# handle = open("output.txt", "w")
# for lin in b:
#     P= "CHECK this waypoint for dublicate",lin,"_______________________"
#     handle.write(str(P) +'\n')
#     print(P)
#     compare1(lin)
#
