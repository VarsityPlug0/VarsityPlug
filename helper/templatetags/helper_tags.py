from django import template
import logging

register = template.Library()

# Set up logging
logger = logging.getLogger('helper')

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

@register.filter
def index(sequence, position, template=None):
    """
    Safely retrieve an item from a sequence by index, returning None if invalid.
    """
    try:
        # Log context for debugging
        context = f"Caller: {template.__file__}" if template and hasattr(template, '__file__') else "Unknown caller"

        # Input validation
        if sequence is None:
            logger.error(f"index: sequence is None [{context}]")
            return None
        if not isinstance(sequence, (list, tuple)):
            logger.error(f"index: sequence is not a list or tuple, got {type(sequence)} [{context}]")
            return None
        if position is None:
            logger.error(f"index: position is None [{context}]")
            return None

        # Convert position to integer
        try:
            pos = int(position)
        except (ValueError, TypeError):
            logger.error(f"index: position is not an integer, got {type(position)}: {position} [{context}]")
            return None

        # Check bounds
        if pos < 0 or pos >= len(sequence):
            logger.debug(f"index: position {pos} out of bounds for sequence of length {len(sequence)} [{context}]")
            return None

        # Safe sequence access
        value = sequence[pos]
        if value is not None:
            value = str(value)  # Ensure safe rendering
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"index: position={pos}, value={value}, type={type(value)} [{context}]")
        return value

    except Exception as e:
        logger.error(f"index error: {str(e)} [{context}]")
        return None

@register.filter
def attr(obj, attr_name):
    """
    Gets an attribute of an object dynamically from a string name
    """
    try:
        return getattr(obj, attr_name)
    except (AttributeError, TypeError):
        try:
            return obj[attr_name]
        except (KeyError, TypeError):
            return None

@register.filter
def get_item(dictionary, key):
    """
    Safely get an item from a dictionary by key.
    Returns None if the key doesn't exist or if the input is invalid.
    """
    try:
        if dictionary is None or not isinstance(dictionary, dict):
            return None
        return dictionary.get(key)
    except Exception as e:
        logger.error(f"get_item error: {str(e)}")
        return None