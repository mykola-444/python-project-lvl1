from argparse import ArgumentParser
from lxml import etree


def convert_report(detailed, brief):
    data = etree.Element('testsuite')
    with open(detailed, "r", encoding="utf-8") as fobj:
        xml = fobj.read()
    root = etree.fromstring(xml.encode('utf8'))
    # TODO: Find all parent suites (hardcoded because it's not necessary)
    classname = "International"
    for iter_test_case in root.iter("test"):
        test_case = etree.SubElement(data, "testcase")
        test_case.set("name", iter_test_case.get("name"))
        test_case.set("classname", classname)
        iter_status_tag = iter_test_case.find("status")
        if iter_status_tag is not None and iter_status_tag.get("status") != "PASS":
            failure = etree.SubElement(test_case, "failure")
            failure.set("message", iter_status_tag.text)
            failure.set("type", "critical")

    with open(brief, "wb") as fobj:
        fobj.write(etree.tostring(data, encoding="utf-8"))


def main():
    parser = ArgumentParser(description="Report analyzer.")
    parser.add_argument("-d", "--detailed_report", type=str,
                        dest="detailed_report",
                        help="Path to detailed xunit report.")
    parser.add_argument("-b", "--brief_report", type=str, dest="brief_report",
                        help="Output brief report.")
    options = parser.parse_args()
    convert_report(options.detailed_report, options.brief_report)


if __name__ == "__main__":
    main()
