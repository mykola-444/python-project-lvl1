class Lib:

    HOW_MANY_JOBS_SHOULD_BE_CHECKED_SDK = 20

    SDK_ROUTING_PROGRAMS = ['olp', 'don', 'bon', 'mtg', 'sup']
    SPARTA_SEARCH_TRAFFIC_COMPONENTS = ['search', 'traffic']
    SPARTA_ROUTING_STREAM = ['spt']
    SPARTA_PSD_COMPONENT = ['psd']
    SPARTA_GUIDANCE_COMPONENT = ['guidance']
    SPARTA_POSITIONING_COMPONENT = ['positioning']
    SPARTA_NDSDAL_COMPONENT = ['ndsdal']

    MITF_FILES_PATH = "map-integration/mitf"

    ROUTING_GEO_NODE = r"geo_node\s=\s[\d|\_|,]*"
    ROUTING_ITEM_NAME = r"item_name\s=\s[\w]*"
    ROUTING_REGION_NAME = r"(?<=\.)[A-Z]*(?=\.test)"
    ROUTING_FILE_NAME = r"(?<=\.)\w*$"
    ROUTING_LDM_FROM_FILE_PATH = r"(?<=[xml\/])([A-Z]*)(?=\/test)"

    STREAMS_FILE_NAME = r"(\_[A-Z]*\_)(\w*\_json)"
    STREAMS_TEST_NAME = r"(\_json\_\_)(\w*)"
    STREAMS_TEXT_BETWEEN_BRACKETS = r"(?<=\()(\w*)(?=\))"

    REGEX_ITEM_AND_NODES = r"(^[a-zA-Z|\_|\d]*)(\:\s\")((\d*\;*\_*\,*)*)"

    PSD_FAILED_TEST = r"(?<=Test\sdata\:\s).*(?=\s->\sResult\:\s\[)"
    PSD_FILE_NAME = r"\w*.json"

    PSD_FILE_LOCATION = r"(?<=Location\:\s).*(?=\:\d*)"
    PSD_FAILED_TEST_NUMBER = r"(?<=--\s\@)(\d\.)(\d*)(?=.*$)"
    PSD_FAILED_TEST_NAME = r"(?<=^).*(?=\s--)"
    PSD_CUT_FILE_NAME = r"\w*\.feature$"
    PSD_REG_ONLY_NUMBER = r"\|\s*\d*\s*\|$"
    PSD_GEO_NODE = r"\|\s*\d{5,}\s*\|"

    GUIDANCE_FILE_NAME = r"[\w|\_]*\.feature"
    GUIDANCE_DATA = r"\|\s[\d|\_|,]*\s\|\)$"
    GUIDANCE_NODE_ID = r"(?<=\|\s).*(?=\s\|\)$)"

    POSITIONING_FILE_NAME = r"[\w|\_]*\.feature"
    POSITIONING_DATA = r"\|\s[\d|\_|,]*\s\|\)$"
    POSITIONING_NODE_ID = r"(?<=\|\s).*(?=\s\|\)$)"

    NDSDAL_ITEM_NAME = r"(?<=item\_name:\s).*(?=;\s)"
    NDSDAL_NODE_ID = r"(?<=geo\_node:\s).*(?=\s})"

    ITEM_NAME = r"^[A-Z]+_*"
    NOT_WORD_ITEM_NAME = r"\W"

    LDM_DATABASE = {
        "WEU": ["AND", "AUT", "BEL", "DEU", "LUX", "VAT", "DNK", "SWE", "FRO", "SJM", "UNI", "GRL", "MLT", "FIN", "FRA",
                "GIB", "ISL", "IRL", "IMN", "ITA", "LIE", "MCO", "SMR", "NLD", "NOR", "PRT", "ESP", "CHE", "GBR", "GGY",
                "JEY"],
        "EEU": ["KOS", "MDA", "MNE", "POL", "SVN", "TJK", "TKM", "UZB", "RUS", "CZE", "GRC", "SRB", "SVK", "TUR", "UKR",
                "BSB", "CUN", "GEO", "CYP", "NCY", "AZE", "ALB", "ARM", "KAZ", "BLR", "KGZ", "BIH", "BGR", "ROU", "HRV",
                "EST", "LVA", "LTU", "MKD", "HUN"],
        "NA": ["UNI", "BHS", "BLZ", "BMU", "VGB", "CAN", "CYM", "CRI", "CUB", "DOM", "SLV", "GTM", "HTI", "HND", "JAM",
               "NIC", "PAN", "SPM", "TCA", "MEX", "PRI", "VIR", "USA"],
        "SAM": ["MSR", "SUR", "SGS", "BRA", "BLM", "BOL", "PRY", "MTQ", "GLP", "CUW", "FLK", "URY", "GUF", "ARG", "ATG",
                "PER", "LCA", "SXM", "VCT", "CHL", "VEN", "GRD", "GUY", "BRB", "ECU", "KNA", "ABW", "AIA", "DMA", "TTO",
                "MAF", "COL", "BES"],
        "SA": ["MSR", "SUR", "SGS", "BRA", "BLM", "BOL", "PRY", "MTQ", "GLP", "CUW", "FLK", "URY", "GUF", "ARG", "ATG",
               "PER", "LCA", "SXM", "VCT", "CHL", "VEN", "GRD", "GUY", "BRB", "ECU", "KNA", "ABW", "AIA", "DMA", "TTO",
               "MAF", "COL", "BES"],
        "APAC": ["BRN", "MMR", "KHM", "TLS", "GUM", "HKG", "IDN", "JPN", "PRK", "LAO", "MAC", "MYS", "MNG", "MNP", "PLW",
                 "PNG", "PHL", "SGP", "SLB", "KOR", "THA", "VNM", "PLI", "SPI", "CHN"],
        "MEA": ["KWT", "ZAF", "REU", "ZWE", "BEN", "SOM", "MRT", "SHN", "GIN", "LBY", "AFG", "ZMB", "COG", "SYC", "GHA",
                "RWA", "IRN", "MWI", "TZA", "BDI", "MUS", "SLE", "LBR", "DJI", "COM", "SEN", "SDN", "CMR", "ISR", "LBN",
                "BWA", "JOR", "SAU", "NAM", "ARE", "LSO", "UNI", "DZA", "AGO", "CAF", "TUN", "GAB", "ETH", "COD", "GNB",
                "SYR", "GMB", "ERI", "STP", "MDG", "GNQ", "TGO", "MOZ", "BHR", "OMN", "SSD", "QAT", "EGY", "MAR", "NGA",
                "GAS", "PSE", "CIV", "TCD", "YEM", "CPV", "SWZ", "KEN", "UGA", "MYT", "BFA", "IRQ", "MLI", "NER", "ESH"],
        "AU": ["AUS", "TON", "CCK", "VUT", "NZL", "FSM", "CXR", "FJI", "ASM", "NFK", "WLF", "PYF", "NCL", "COK", "WSM",
               "NRU", "UNI", "TUV", "NIU", "PCN", "KIR", "MHL", "TKL"],
        "IND": ["BGD", "LKA", "NPL", "MDV", "IND", "IOT", "BTN", "PAK"]
    }

    TEST_REPORT = "xunit.xml"
    TEST_REPORTS_ARCHIVE = "test_reports.tar.gz"

    POSITIONING_REPORT_PREFIX = "sparta_TEST"
    GUIDANCE_REPORT_PREFIX = "TEST"
    PSD_REPORT_PREFIX = "TEST"

    SDK_JENKINS_JOBS = {
        "don": ["https://mos.cci.in.here.com/job/team-routing/job/client/job/test-integration-nds-donington-only-car-mitf",
                "https://mos.cci.in.here.com/job/team-routing/job/hybrid/job/test-integration-nds-donington-only-car-brf-mitf"],
        "bon": ["https://mos.cci.in.here.com/job/team-routing/job/client/job/test-integration-nds-bonneville-only-car-mitf",
                "https://mos.cci.in.here.com/job/team-routing/job/hybrid/job/test-integration-nds-bonneville-only-car-brf-mitf"],
        "mtg": ["https://mos.cci.in.here.com/job/team-routing/job/client/job/test-integration-nds-vanilla-only-car-mitf",
                "https://mos.cci.in.here.com/job/team-routing/job/hybrid/job/test-integration-nds-vanilla-only-car-brf-mitf"],
        "sup": ["https://mos.cci.in.here.com/job/team-routing/job/client/job/test-integration-nds-superset-only-car-mitf"]
    }
