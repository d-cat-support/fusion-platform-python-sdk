"""
General utilities.

author: Matthew Casey

&copy; [Digital Content Analysis Technology Ltd](https://www.d-cat.co.uk)
"""

from datetime import date, datetime, time, timezone
from decimal import Decimal
import re
from types import MappingProxyType


def datetime_parse(string_or_blank):
    """
    Attempts to parse an ISO8601 datetime from a string using common formats.

    Args:
        string_or_blank: The datetime to parse, or blank.

    Returns:
        The parsed datetime or None if not parsable or blank.
    """
    parsed = None

    if not string_blank(string_or_blank):
        # Strip out all optional delimiters and then attempt to parse with and without the "Z".
        stripped = re.sub(r"[:]|([-](?!((\d{2}[:]\d{2})|(\d{4}))$))", '', str(string_or_blank))
        formats = ['%Y%m%dT%H%M%S.%f', '%Y%m%dT%H%M%S.%f%z', '%Y%m%dT%H%M%S', '%Y%m%dT%H%M%S%z']

        for format in formats:
            try:
                parsed = datetime.strptime(stripped, format)
                parsed = parsed.astimezone(timezone.utc) if parsed.tzinfo is None else parsed  # Assume UTC if no timezone is provided.
            except:
                pass

            if parsed is not None:
                break

    return parsed


def dict_nested_get(dictionary_or_value, keys, default=None):
    """
    Performs a dictionary.get(key, default) using the supplied list of keys assuming that each successive key is nested.

    For example, for a dictionary dictionary = { "key1": { "key2": 1 } }, use nested_get(dictionary, ["key1", "key2"]) to get the value of "key2".

    Args:
        dictionary_or_value: The dictionary to get the value from or the value itself from this recursive method.
        keys: The list of nested keys.
        default: The default value to return if no value exists. Default is None.

    Returns:
        The value of the nested key or the default if not found.
    """
    if isinstance(dictionary_or_value, dict) and isinstance(keys, list) and (len(keys) > 1):
        key = keys.pop(0)
        return dict_nested_get(dictionary_or_value.get(key, default), keys, default)
    elif isinstance(dictionary_or_value, dict) and isinstance(keys, list) and (len(keys) == 1):
        return dictionary_or_value.get(keys[0], default)
    elif (dictionary_or_value is not None) and (not isinstance(dictionary_or_value, dict)):
        return dictionary_or_value
    else:
        return default


def json_default(value):
    """
    Used during JSON serialisation for objects which cannot be serialised. This will attempt to convert the values and otherwise return a string.

    Args:
        value: The value to serialise.

    Returns:
        The serialised value.
    """
    if isinstance(value, time) or isinstance(value, date) or isinstance(value, datetime):
        # Convert datetimes. Note that if the datetime does not have a timezone, we enforce UTC. See also fields.DateTime#_serialize.
        value = value.astimezone(timezone.utc) if isinstance(value, datetime) and (value.tzinfo is None) else value
        return value.isoformat()
    elif isinstance(value, Decimal):
        # We want to output numbers as either integers (no trailing ".0") or floats. This will also convert decimals.
        return int(value) if float(value).is_integer() else float(value)
    elif isinstance(value, MappingProxyType):
        # Read-only dictionaries may be defined using the MappingProxyType. For serialisation, we therefore convert them back to dictionaries.
        return dict(value)
    else:
        return str(value)


def string_blank(string_or_blank):
    """
    Checks if a string is None or blank.

    Args:
        string_or_blank: The string to check.

    Returns:
        True if the string is None, blank ("") or just made up with spaces.
    """
    return (string_or_blank is None) or (not bool(string_or_blank.strip()))


def string_camel_to_underscore(string):
    """
    Converts a camel case string to underscore case.

    Args:
        string: The string to convert.

    Returns:
        The converted string.
    """

    return ''.join(['_' + i.lower() if i.isupper() else i for i in string]).lstrip('_').lower() if string is not None else None


def value_from_read_only(value):
    """
    Takes a value and makes it writable. This recursive method will deal with dictionaries and lists. Here, dictionaries are assumed to be mapping proxies, while
    tuples are assumed to be lists.

    Args:
        value: The value to make read-only.

    Returns:
        The read-only value.
    """
    if isinstance(value, MappingProxyType):
        return dict({inner_key: value_from_read_only(inner_value) for inner_key, inner_value in value.items()})  # Creates a mutable mapping.
    elif isinstance(value, tuple):  # This assumes that tuples are really lists.
        return list([value_from_read_only(inner_value) for inner_value in value])  # Creates a mutable list.
    else:
        return value


def value_to_read_only(value):
    """
    Takes a value and makes it read-only. This recursive method will deal with dictionaries and lists. This method will not deal with objects that are immutable,
    such as datetimes, but rather makes sure that the references to objects cannot be changed. For example, dictionary values cannot be replaced or list items
    removed.

    Args:
        value: The value to make read-only.

    Returns:
        The read-only value.
    """
    if isinstance(value, dict):
        return MappingProxyType({inner_key: value_to_read_only(inner_value) for inner_key, inner_value in value.items()})  # Creates an immutable mapping.
    elif isinstance(value, list):
        return tuple([value_to_read_only(inner_value) for inner_value in value])  # Creates an immutable list, which is just a tuple.
    else:
        return value


def value_to_string(value):
    """
    Used to convert any value into a useful string representation. For example, datetimes into ISO format. Also handles other type conversions to make them pretty.

    Args:
        value: The value to convert to a string.

    Returns:
        The corresponding (pretty) string value.
    """
    if isinstance(value, list) or isinstance(value, tuple):
        return f"[{', '.join([value_to_string(inner) for inner in value])}]"
    elif isinstance(value, dict):
        items = [f"{key}: {value_to_string(inner)}" for key, inner in value.items()]
        return f"{{{', '.join(items)}}}"
    else:
        # Return whatever is appropriate for JSON, but as a string.
        return str(json_default(value))
