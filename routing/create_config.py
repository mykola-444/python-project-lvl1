from argparse import ArgumentParser
from configparser import ConfigParser


def generate_config(config, config_file, params):
    """
    Updates previous config file
    """
    config.read(config_file)
    for pair in params:
        key, value = tuple(pair.split("="))
        if config.has_option("GeneratorSection", key):
            config["GeneratorSection"][key] = value
        elif config.has_option("RunnerSection", key):
            config["RunnerSection"][key] = value
        else:
            err_message = "Undetermined option: '%s'\n" \
                          "Available options in " \
                          "GeneratorSection: %s" \
                          "RunnerSection: %s" % (key,
                                                 config["GeneratorSection"].keys(),
                                                 config["RunnerSection"].keys())
            raise Exception(err_message)
        print("Updated %s=%s" % (key, value))


def main():
    opt_parser = ArgumentParser()
    opt_parser.add_argument("--config_template", dest="config_template",
                            help="Path config template", required=True)
    opt_parser.add_argument("--output", dest="output", help="Output config "
                            " file", required=True,)
    opt_parser.add_argument("--params", dest="params", help="Config parameters."
                            " Pairs like PARAM_NAME=PARAM_VALUE", nargs='*')
    options = opt_parser.parse_args()
    config = ConfigParser()
    generate_config(config, options.config_template, options.params)
    with open(options.output, "w") as _file:
        config.write(_file)
    print("Created config: '%s'" % (options.output))
    print("Done!")


if __name__ == "__main__":
    main()
