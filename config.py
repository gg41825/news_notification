import configparser

config = configparser.ConfigParser()
config.allow_no_value = True
config.read('service.conf')