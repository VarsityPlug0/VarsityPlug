from django import template
import logging

register = template.Library()

# Set up logging
logger = logging.getLogger('helper')

# Flag to ensure deprecation warning is logged only once
DEPRECATION_WARNING = True

@register.filter
def get_item(dictionary, key, template=None):
    """
    Safely retrieve a value from a dictionary by key, returning None if invalid.
    Note: This filter is redundant with 'lookup' and may be deprecated in future versions.
    """
    global DEPRECATION_WARNING
    try:
        # Log deprecation warning once in DEBUG mode
        if DEPRECATION_WARNING and logger.isEnabledFor(logging.DEBUG):
            logger.debug("get_item filter is deprecated; use 'lookup' instead")
            DEPRECATION_WARNING = False

        # Log context for debugging (limited in production)
        context = f"Caller: {template.__file__}" if template and hasattr(template, '__file__') else "Unknown caller"

        # Input validation
        if dictionary is None:
            logger.error(f"get_item: dictionary is None [{context}]")
            return None
        if not isinstance(dictionary, dict):
            logger.error(f"get_item: dictionary is not a dict, got {type(dictionary)} [{context}]")
            return None
        if key is None:
            logger.error(f"get_item: key is None [{context}]")
            return None
        if not isinstance(key, str):
            logger.error(f"get_item: key is not a string, got {type(key)}: {key} [{context}]")
            return None

        # Check for empty dictionary
        if not dictionary:
            logger.debug(f"get_item: dictionary is empty for key={key} [{context}]")
            return None

        # Safe dictionary access
        value = dictionary.get(key)
        if value is not None:
            value = str(value)  # Ensure safe rendering
        # Log only in DEBUG mode to reduce production overhead
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"get_item: key={key}, value={value}, type={type(value)} [{context}]")
        return value

    except Exception as e:
        logger.error(f"get_item error: {str(e)} [{context}]")
        return None

@register.filter
def lookup(dictionary, key, template=None):
    """
    Safely lookup a key in a dictionary, returning None if the key is missing or invalid.
    """
    try:
        # Log context for debugging (limited in production)
        context = f"Caller: {template.__file__}" if template and hasattr(template, '__file__') else "Unknown caller"

        # Input validation
        if dictionary is None:
            logger.error(f"lookup: dictionary is None [{context}]")
            return None
        if not isinstance(dictionary, dict):
            logger.error(f"lookup: dictionary is not a dict, got {type(dictionary)} [{context}]")
            return None
        if key is None:
            logger.error(f"lookup: key is None [{context}]")
            return None
        if not isinstance(key, str):
            logger.error(f"lookup: key is not a string, got {type(key)}: {key} [{context}]")
            return None

        # Check for empty dictionary
        if not dictionary:
            logger.debug(f"lookup: dictionary is empty for key={key} [{context}]")
            return None

        # Safe dictionary access
        value = dictionary.get(key, None)
        if value is not None:
            value = str(value)  # Ensure safe rendering
        # Log only in DEBUG mode to reduce production overhead
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"lookup: key={key}, value={value}, type={type(value)} [{context}]")
        return value

    except Exception as e:
        logger.error(f"lookup error: {str(e)} [{context}]")
        return None