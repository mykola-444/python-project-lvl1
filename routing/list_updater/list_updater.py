import argparse
import logging

from common_data import Data
from upd_guidance import SpartaGuidanceStream
from upd_library import Lib
from upd_ndsdal import SpartaNdsDalStream
from upd_positioning import SpartaPositioningStream
# from upd_psdsrm_behave import SpartaPSDBehaveStream
from upd_psdsrm_feature import SpartaPSDFeatureStream
from upd_sdk_routing import SDKRoutingStream
from upd_sparta_routing import SpartaRoutingStream
from upd_sparta_streams import SpartaStreams


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--change-id", dest="change_id", required=False,
                        help="Map config review number.\
                              For example: 1341926")
    parser.add_argument("--jenkins-job", dest="jenkins_job", required=False,
                        help="Name of Jenkins job that result contains failed MITF tests.\
                              For example: psv-mitf-ngeo-func-json-nds-sparta-rw-linux-x86-gcc5.4")
    parser.add_argument("--key", dest="key", required=True,
                        help="Key of SDK program or component of Sparta program that contains\
                              failed MITF tests.\
                              SDK program key can be one of the next: 'olp', 'don', 'bon', 'mtg', 'sup'.\
                              Sparta stream key can be one of the next: 'routing', 'search', 'traffic', 'ndsdal',\
                              'guidance', 'positioning', 'psd")
    parser.add_argument("--investigation-list", dest="investigation_list", required=True,
                        help="Name of investigation list. "
                             "For example: nds_2.5.2_investigation_list.yaml")
    parser.add_argument("--job-url", dest="job_url", required=False,
                        help="URL of the build that contains failed MITF tests.")
    parser.add_argument("--update-flag", dest="update_flag", action="store_true", required=False,
                        help="Investigation list will be updated and uploaded to S3.")
    return parser.parse_args()


def main(config):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Main")
    logger.info(" Script is running with parameters: \n\t{}".format(config))

    if config.key in Lib.SPARTA_ROUTING_STREAM:
        task = SpartaRoutingStream(config)
    elif config.key in Lib.SPARTA_SEARCH_TRAFFIC_COMPONENTS:
        task = SpartaStreams(config)
    # elif config.key in Lib.SPARTA_PSD_COMPONENT \
    #         and Data.check_input_files_type(folder='team-psd', ext_name='json',
    #                                         destination=Lib.MITF_FILES_PATH):
    #     task = SpartaPSDBehaveStream(config)
    elif config.key in Lib.SPARTA_PSD_COMPONENT \
            and Data.check_input_files_type(folder='team-psd', ext_name='feature',
                                            destination=Lib.MITF_FILES_PATH):
        task = SpartaPSDFeatureStream(config)
    elif config.key in Lib.SPARTA_GUIDANCE_COMPONENT:
        task = SpartaGuidanceStream(config)
    elif config.key in Lib.SPARTA_POSITIONING_COMPONENT:
        task = SpartaPositioningStream(config)
    elif config.key in Lib.SPARTA_NDSDAL_COMPONENT:
        task = SpartaNdsDalStream(config)
    else:
        task = SDKRoutingStream(config)

    geo_data = task.run_calculation()

    if geo_data:
        updated_list = Data.collect_updated_investigation_list(geo_data, config.investigation_list)
    else:
        logger.error("WARNING: There is not enough data to complete update. "
                     "Script is stopped.".upper())
        raise ValueError("'geo_data' is empty.")

    if config.update_flag:
        Data.write_investigation_list(updated_list, config.investigation_list)


if __name__ == '__main__':
    input_config = get_config()
    main(input_config)
