from django import template
import logging

register = template.Library()

# Set up logging
logger = logging.getLogger('helper')

@register.filter
def get_item(dictionary, key):
    """
    Safely retrieve a value from a dictionary by key, returning None if invalid.
    """
    try:
        # Check if dictionary is None or not a dict
        if dictionary is None:
            logger.error("get_item: dictionary is None")
            return None
        if not isinstance(dictionary, dict):
            logger.error(f"get_item: dictionary is not a dict, got {type(dictionary)}")
            return None
        # Check if key is None or not a string
        if key is None:
            logger.error("get_item: key is None")
            return None
        if not isinstance(key, str):
            logger.error(f"get_item: key is not a string, got {type(key)}: {key}")
            return None
        # Check if dictionary is empty
        if not dictionary:
            logger.debug(f"get_item: dictionary is empty for key={key}")
            return None
        value = dictionary.get(key)
        # Convert value to string to ensure safe rendering
        if value is not None:
            value = str(value)
        logger.debug(f"get_item: key={key}, value={value}, type={type(value)}")
        return value
    except Exception as e:
        logger.error(f"get_item error: {str(e)}")
        return None

@register.filter
def lookup(dictionary, key):
    """
    Safely lookup a key in a dictionary, returning None if the key is missing or invalid.
    """
    try:
        # Check if dictionary is None or not a dict
        if dictionary is None:
            logger.error("lookup: dictionary is None")
            return None
        if not isinstance(dictionary, dict):
            logger.error(f"lookup: dictionary is not a dict, got {type(dictionary)}")
            return None
        # Check if key is None or not a string
        if key is None:
            logger.error("lookup: key is None")
            return None
        if not isinstance(key, str):
            logger.error(f"lookup: key is not a string, got {type(key)}: {key}")
            return None
        # Check if dictionary is empty
        if not dictionary:
            logger.debug(f"lookup: dictionary is empty for key={key}")
            return None
        value = dictionary.get(key, None)
        # Convert value to string to ensure safe rendering
        if value is not None:
            value = str(value)
        logger.debug(f"lookup: key={key}, value={value}, type={type(value)}")
        return value
    except Exception as e:
        logger.error(f"lookup error: {str(e)}")
        return None