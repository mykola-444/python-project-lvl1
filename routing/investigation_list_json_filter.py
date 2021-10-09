# encoding: utf-8

import fnmatch
import io
import json
import logging
import os
from argparse import ArgumentParser

from generate_data_by_predefined_geo_nodes import create_investigation_list

"""Logging settings"""
LOG_NAME = __name__
LOG_FORMAT = "[%(asctime)s] [%(levelname)-7s] --- %(message)s (%(filename)s:%(lineno)s)"

"""Initialize logging routine"""
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(name=LOG_NAME)

investigation_list, countries = dict(), list()
item_names = {
    "right_turn_lane_assistance_data": "right_turn_lanes",
    "tts_drive_towards_signpost": "text_to_speech_drive_18",
    "tts_drive_towards_signpost_continue_other_highway": "text_to_speech_drive_42",
    "tts_drive_towards_signpost_leave_highway": "text_to_speech_drive_44",
    "tts_drive_towards_signpost_continue_same_highway": "text_to_speech_drive_45",
    "signpost_directions_data": "signpost_directions",
    "text_to_speech_drive_junction": "text_to_speech_drive_19",
    "text_to_speech_drive_highway": "text_to_speech_drive_64",
    "case_end_bridge_above": "end_bridge_above",
    "case_outside_tunnel_attribute": "outside_tunnel_attribute",
    "case_1_acceleration_left_lane": "1_acceleration_lane_left",
    "case_2_acceleration_left_lane": "2_acceleration_lane_left",
    "case_3_acceleration_left_lane": "3_acceleration_lane_left",
    "case_1_deceleration_left_lane": "1_deceleration_lane_left",
    "case_2_deceleration_left_lane": "2_deceleration_lane_left",
    "case_3_deceleration_left_lane": "3_deceleration_lane_left",
    "case_1_acceleration_right_lane": "1_acceleration_lane_right",
    "case_2_acceleration_right_lane": "2_acceleration_lane_right",
    # "case_3_acceleration_left_lane": "3_or_more_acceleration_lane_left",
    "case_3_acceleration_right_lane": "3_or_more_acceleration_lane_right",
    "case_1_deceleration_right_lane": "1_deceleration_lane_right",
    "case_2_deceleration_right_lane": "2_deceleration_lane_right",
    "case_3_deceleration_right_lane": "3_or_more_deceleration_lane_right",
    "case_start_bridge_above": "start_bridge_above",
    "case_inside_tunnel_attribute": "inside_tunnel_attribute",
    "case_turning_lane_right_attribute": "turning_lane_right_attribute",
    "case_two_turning_lane_right_attribute": "two_turning_lane_right_attribute",
    "case_two_turning_lane_attribute": "two_turning_lane_attribute",
    "case_two_acceleration_lane_right_attribute": "two_acceleration_lane_right_attribute",
    "case_turning_lane_left_attribute": "turning_lane_left_attribute",
    "case_one_aux_lane_right_attribute": "one_aux_lane_right_attribute",
    "case_most_probable_path": "most_probable_path"
}


def is_in_investigation_list(item_name, node):
    if item_name in investigation_list:
        return investigation_list[item_name]["skip_all"] or \
            (str(node) in investigation_list[item_name]['geo_nodes'])
    else:
        return False


def is_removing(test):
    if 'debug_data' in test and 'item_name' in test['debug_data'] and \
            'geo_node' in test['debug_data'] and 'country' in test:
        item_name = test['debug_data']['item_name']
        if item_name in item_names:
            item_name = item_names[item_name]
        if "exit_number_attribute" in item_name:
            item_name = "_".join(item_name.split("_")[1:])
        if "traffic_flow" in item_name:
            item_name = "_".join(item_name.split("_")[:-1])
        geo_node = test['debug_data']['geo_node']
        if is_in_investigation_list(item_name, geo_node):
            print("Test removed by investigation list: "
                  "debug_data = {}; country: {}".format(test['debug_data'], test['country']))
            return True
        for country in test['country']:
            if countries and country not in countries:
                print("Test removed by country not in region: "
                      "debug_data = {}; country: {}".format(test['debug_data'], test['country']))
                return True
    return False


def filtering_tests(tests):
    removed_test = 0
    original_tests = tests.copy()
    for test in original_tests:
        if is_removing(test):
            tests.remove(test)
            removed_test += 1
    return removed_test


def remove_tests(path):
    jsons = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.json'):
            jsons.append(os.path.join(root, filename))
    logger.info("{} - JSONS files under analysis:".format(len(jsons)))
    removed_test = 0
    for fname in jsons:
        with io.open(fname, "r+", encoding="utf-8") as fd:
            output = json.loads(fd.read())
            if "tests" in output:
                removed = filtering_tests(output['tests'])
                if removed > 0:
                    if output['tests']:
                        fd.seek(0)
                        fd.write(json.dumps(output, ensure_ascii=False))
                        fd.truncate()
                    else:
                        os.unlink(fname)
                removed_test += removed
            else:
                if is_removing(output):
                    fd.close()
                    os.unlink(fname)
                    removed_test += 1
    return removed_test


def main():
    logger.info("starting investigation...")
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--investigation_list", dest="investigation_list",
                            help="Investigation list yaml file", required=True)
    opt_parser.add_argument("--jsons_path", dest="jsons_path",
                            help="Path to the test JSON files folder", required=True)
    opt_parser.add_argument("--market", dest="market",
                            help="Filter tests by country in market", required=False)
    opt_parser.add_argument("--filter", dest="filter", default="sparta_nds_countries.json",
                            help="JSON file describe iso country code include in region. "
                                 "Filter tests by country in market", required=False)
    options = opt_parser.parse_args()

    investigation_list.update(create_investigation_list(options.investigation_list))
    if options.market:
        with io.open(options.filter) as fd:
            output = json.load(fd)
        countries.extend(output[options.market])
    removed_tests = remove_tests(options.jsons_path)
    logger.info("investigation done\n")
    logger.warning("{} tests have been removed".format(removed_tests))


if __name__ == '__main__':
    main()
