"""
Parses xunit.xml report and performs "smart_analysis"
"""
from argparse import ArgumentParser
from lxml import etree
import sys


THRESHOLD = 0.7
CSS = """
<style media="all" type="text/css">
/* Generic and misc styles */
body {
    font-family: Helvetica, sans-serif;
    font-size: 0.8em;
    color: black;
    padding: 6px;
    background: white;
}
table {
    table-layout: fixed;
    word-wrap: break-word;
    empty-cells: show;
    font-size: 1em;
}
th, td {
    vertical-align: top;
}
th {
    cursor: pointer;
}
br {
    mso-data-placement: same-cell; /* maintain line breaks in Excel */
}
hr {
    background: #ccc;
    height: 1px;
    border: 0;
}
a, a:link, a:visited {
    text-decoration: none;
    color: #15c;
}
a > img {
    border: 1px solid #15c !important;
}
a:hover, a:active {
    text-decoration: underline;
    color: #61c;
}
.parent-name {
    font-size: 0.7em;
    letter-spacing: -0.07em;
}
.tc_name {
    font-size: 1em;
}
.last {
    padding: 0px 50px;
}
</style>
"""
BASE = """
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
{}
</head>
<body>
<table class="statistics" id="table">
<tbody>
<tr><th>TC Name</th><th>Result</th><th>Score</th></tr>
{}
</tbody>
</table>
{}
</body>
</html>
"""

JS = """
<script type="text/javascript">
        const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;

const comparer = (idx, asc) => (a, b) => ((v1, v2) =>
    v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
    )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

// do the work...
document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
    const table = th.closest('table');
    Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
        .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
        .forEach(tr => table.appendChild(tr) );
})));
</script>
"""


SQUARE = """<svg width="5" height="5">
<rect width="5" height="5" style="fill:{};stroke-width:0;stroke:rgb(0,0,0)" /></svg> """


def parse_report(report):
    """
    Parses xunit.xml (production) report.
    Returns statistic of passed test cases:
    {"TC_NAME": [[0, 1, ..., MAX_INDEX], TOTAL_TEST_CASE_NUMBER]}
    """
    with open(report, encoding="utf-8") as fobj:
        xml = fobj.read()
    root = etree.fromstring(xml.encode('utf8'))
    stats = dict()
    for test_case in root.iter("testcase"):
        tc_classname = test_case.get("classname")
        tc_name = test_case.get("name")
        tc_index = None
        if not tc_name:
            continue
        tc_name = "{}|{}".format(tc_classname, tc_name)
        if tc_name[-1].isdigit():
            tc_index = tc_name[tc_name.rfind(" ") + 1:]
            tc_name = tc_name[:tc_name.rfind(" ")]
        else:
            # TODO: check this
            # Skip original test cases
            continue
        if not stats.get(tc_name):
            stats[tc_name] = [list(), 0]
        failure = test_case.find("failure")
        if failure is None:
            stats[tc_name][0].append(tc_index)
        else:
            stats[tc_name][0].append(None)

        {}
        stats[tc_name][1] += 1
    return stats


def analyze_stats(stats):
    # TODO (asmirnov): Extend this function to be "more smart"
    smart_results = dict()
    for tc_name, value in stats.items():
        passed = len([i for i in value[0] if i is not None])
        if passed >= value[1] * THRESHOLD:
            smart_results[tc_name] = {"result": "passed"}
        else:
            smart_results[tc_name] = {"result": "failed"}
        smart_results[tc_name].update({"passed": passed,
                                       "total": value[1],
                                       "details": value[0]})
    return smart_results


def save_final_report(smart_results, output_report):
    print("Creating analyzed xunit report...")
    total_tests = len(smart_results.keys())
    total_failures = 0
    for item in smart_results:
        if smart_results[item]["result"] == "failed":
            total_failures += 1
    page = etree.Element(
        "testsuite",
        name="International",
        tests=str(total_tests),
        errors="0",
        failures=str(total_failures),
        skipped="0",
        time="0.0"
    )
    final_report = etree.ElementTree(page)
    for item in smart_results:
        classname, name = tuple(item.split("|"))
        pageElement = etree.SubElement(
            page,
            'testcase',
            classname=classname,
            name=name,
            time="0.0"
        )
        if smart_results[item]["result"] == "failed":
            errorElement = etree.SubElement(
                pageElement,
                "failure",
                message="Test failed due to not getting into defined threshold (%s)."
                        "Please see full report for original failure of each test" % (THRESHOLD, ),
                type="ThresholdError"
            )
            errorElement.text = "\n"
        else:
            pageElement.text = "\n"
    final_report.write(output_report, xml_declaration=True, encoding='utf-8', pretty_print=True)


def create_html(smart_results, html_report, xunit):
    print("Creating html...")
    rows = ""
    for item in smart_results:
        details = ""
        for value in smart_results[item]["details"]:
            if value is None:
                details += SQUARE.format("red")
            else:
                details += SQUARE.format("green")
        arr = item.split("|")
        suite, name = arr[0], arr[1]
        rows += ("<tr><td><a href='report.html'><span class='parent'>{}</span>.</a>"
                 "<a href='report.html'><b><span class='tc_name'>{}</span></b></a></td><td>{}</td>"
                 "<td class='last'><p style='color:{}'>{}</p></td></tr>").format(
            suite, name, details,
                     "green" if smart_results[item][
                         "result"] == "passed" else "red", "{:.2f}".format(
                         smart_results[item]["passed"] * 100 / smart_results[item]["total"]))
    content = BASE.format(CSS, rows, JS)

    with open(html_report, "w") as f_:
        f_.write(content)
        f_.close()


def main():
    parser = ArgumentParser(description="Report analyzer.")
    parser.add_argument("-i", "--input_report", type=str, dest="input_report",
                        help="Path to original xunit report.", required=True)
    parser.add_argument("-o", "--output_report", type=str, dest="output_report",
                        help="Path to analyzed xunit report.", required=True)
    parser.add_argument("-s", "--static_html", type=str, dest="static_html",
                        help="Path to html report.", default="analyzed_xunit.html")

    options = parser.parse_args()
    exit_code = 0
    smart_results = analyze_stats(parse_report(options.input_report))
    create_html(smart_results, options.static_html, options.input_report)
    if "failed" in [value["result"] for value in smart_results.values()]:
        exit_code = 1
    save_final_report(smart_results, options.output_report)
    print("Done!")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
