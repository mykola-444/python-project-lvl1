import json
from argparse import ArgumentParser
from json2html import json2html


def update_dict_keys(obj, mapping_dict):
    if isinstance(obj, dict):
        return {mapping_dict[k]: update_dict_keys(v, mapping_dict) for k, v in obj.items()}
    else:
        return obj


def main():
    parser = ArgumentParser(description="Convert json coverage report to html")
    parser.add_argument("-i", "--input", type=str, dest="input_report",
                        help="Path to input json report.", required=True)
    options = parser.parse_args()
    test_counter = 0
    mapping_dict = dict()
    with open(options.input_report, "r") as fh:
        report_data = json.loads(fh.read())
        for gen in report_data:
            gen_counter = 0
            for item_name in report_data[gen]:
                gen_counter += len(report_data[gen][item_name])
                test_counter += len(report_data[gen][item_name])
                mapping_dict[item_name] = "%s (%s)" % (item_name, len(report_data[gen][item_name]))
            mapping_dict[gen] = "%s (%s)" % (gen, gen_counter)
        report_data = update_dict_keys(report_data, mapping_dict)
        html_table = json2html.convert(json.dumps(report_data))
    print("Tests covered (total):", test_counter)
    print(html_table)


if __name__ == "__main__":
    main()
