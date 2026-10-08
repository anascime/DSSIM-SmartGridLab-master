import logging
import logging.config
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config['logging'])

# Now, any module where __name__ starts with `my_app` will use the config.
# logger = logging.getLogger(__name__)

# logger.debug("This is a debug message.") # will be dropped due to `console` handler level
# logger.info("Application starting up with configuration from YAML.")
# logger.warning("This is a warning.")
