import argparse

from confluence.aepreq_report import AepreqReport
from confluence.test_summary_report import TestSummaryReport
from traceability_matrix.generate_traceability_matrix import TraceabilityMatrixGenerator
from zephyr.reporting import Reporting
from logger import Logger

log = Logger(" Main Reporting ").log

parser = argparse.ArgumentParser()

parser.add_argument('--create_cycle', type=bool, default=False, const=True, nargs='?', help='For creating zephyr cycle')
parser.add_argument('--project', type=str, required=False, help="Using for creating zephyr cycle")
parser.add_argument('--zephyr_build', type=str, required=False, help="Use for creating zephyr cycle")
parser.add_argument('--cycle_name', type=str, required=False,
                    help="Use for creating zephyr cycle and aepreq report, and traceability_matrix")
parser.add_argument('--report_path', type=str, required=False, help="Use for creating zephyr cycle")
parser.add_argument('--description', type=str, required=False, help="Use for creating  zephyr cycle")

parser.add_argument('--confluence_aepreq_report', type=bool, default=False, const=True, nargs='?',
                    help="Use for creating aepreq report")
parser.add_argument('--aepreqs', type=str, required=False,
                    help="Use for creating aepreq reports  Example: AEPREQ-1234 AEPREQ-1235")
parser.add_argument('--fix_version', type=str, required=False,
                    help="Use for creating aepreq, test summary reports and and traceability_matrix")
parser.add_argument('--map_version', type=str, required=False, help="Use for creating aepreq report")
parser.add_argument('--map_revision', type=str, required=False, help="Use for creating aepreq report")
parser.add_argument('--map_region', type=str, default="World", help="Use for creating aepreq report")
parser.add_argument('--platform', type=str, default='Linux64', help="Use for creating aepreq report")

parser.add_argument('--confluence_test_summary_report', type=bool, default=False, const=True, nargs='?',
                    help="Use for creating test summary report")
parser.add_argument('--blank_page', type=bool, default=False, const=True, nargs='?',
                    help="Use for creating test summary report")

parser.add_argument('--traceability_matrix', type=bool, default=False, const=True, nargs='?',
                    help="Use for creating traceability_matrix")
parser.add_argument('--aeport', type=str, required=False, help="Use for creating traceability_matrix")


def create_zephyr_cycle(data):

    cycle_params = [
        data.project,
        data.zephyr_build,
        data.cycle_name,
        data.report_path
        ]
    cycle_description = data.description

    Reporting(*cycle_params).sync_results(cycle_description)


def create_confluence_aepeq_report(data):
    aepreqs = data.aepreqs.split(' ')
    for aepreq in aepreqs:
        log.info(f'Started creating report for {aepreq}')
        AepreqReport(aepreq_jira_key=aepreq,
                     fix_version=data.fix_version,
                     cycle_name=data.cycle_name,
                     map_version=data.map_version,
                     map_revision=data.map_revision,
                     map_region=data.map_region,
                     platform=data.platform,
                     ).create_page()


def create_test_summary_confluence_report(data):
    TestSummaryReport(data.fix_version).create_page(data.blank_page)


def create_traceability_matrix(data):

    TraceabilityMatrixGenerator(data.fix_version, data.cycle_name, data.aeport).create_page()


if __name__ == '__main__':

    args = parser.parse_args()

    create_cycle = args.create_cycle
    if create_cycle:
        create_zephyr_cycle(args)

    confluence_aepreq_report = args.confluence_aepreq_report
    if confluence_aepreq_report:
        create_confluence_aepeq_report(args)

    confluence_test_summary_report = args.confluence_test_summary_report
    if confluence_test_summary_report:
        create_test_summary_confluence_report(args)

    traceability_matrix = args.traceability_matrix
    if traceability_matrix:
        create_traceability_matrix(args)
