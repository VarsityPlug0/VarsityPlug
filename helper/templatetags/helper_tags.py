from django import template
import logging
import traceback

register = template.Library()

# Set up logging
logger = logging.getLogger('helper')

@register.filter
def get_item(dictionary, key):
    """
    Safely retrieve a value from a dictionary by key, returning None if invalid.
    """
    try:
        # Log context for debugging
        stack = traceback.extract_stack(limit=3)
        caller = stack[-2] if len(stack) >= 2 else None
        context = f"Caller: {caller.filename}:{caller.lineno}" if caller else "Unknown caller"

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
        logger.debug(f"get_item: key={key}, value={value}, type={type(value)} [{context}]")
        return value

    except Exception as e:
        logger.error(f"get_item error: {str(e)} [{context}]")
        return None

@register.filter
def lookup(dictionary, key):
    """
    Safely lookup a key in a dictionary, returning None if the key is missing or invalid.
    """
    try:
        # Log context for debugging
        stack = traceback.extract_stack(limit=3)
        caller = stack[-2] if len(stack) >= 2 else None
        context = f"Caller: {caller.filename}:{caller.lineno}" if caller else "Unknown caller"

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
        logger.debug(f"lookup: key={key}, value={value}, type={type(value)} [{context}]")
        return value

    except Exception as e:
        logger.error(f"lookup error: {str(e)} [{context}]")
        return None