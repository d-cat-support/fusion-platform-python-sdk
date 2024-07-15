#
# Utilities test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from collections import OrderedDict
from datetime import date, datetime, time, timezone
from decimal import Decimal
from types import MappingProxyType

import pytest
import pytz

from tests.custom_test_case import CustomTestCase

from fusion_platform.common.utilities import datetime_parse, dict_nested_get, json_default, string_blank, string_camel_to_underscore, value_from_read_only, \
    value_to_read_only, value_to_string


class TestUtilities(CustomTestCase):
    def test_datetime_parse(self):
        """
        Tests datetime_parse.
        """
        now = datetime.now()
        now_utc = datetime.now(tz=timezone.utc)

        self.assertIsNone(datetime_parse(None))
        self.assertIsNone(datetime_parse(''))
        self.assertIsNone(datetime_parse(' '))
        self.assertEqual(now.astimezone(timezone.utc), datetime_parse(now.isoformat()))
        self.assertEqual(now_utc, datetime_parse(now_utc.isoformat()))

    def test_dict_nested_get_none(self):
        """
        Tests dict_nested_get with no dictionary.
        """
        self.assertIsNone(dict_nested_get(None, None))
        self.assertIsNone(dict_nested_get({'test': 'value'}, None))
        self.assertIsNone(dict_nested_get({'test': 'value'}, []))
        self.assertIsNone(dict_nested_get({'test1': {'test2': 'value'}}, ['unknown']))

    def test_dict_nested_get_default(self):
        """
        Tests dict_nested_get with a default value.
        """
        self.assertEqual(1, dict_nested_get(None, None, 1))
        self.assertEqual(1, dict_nested_get({'test': 'value'}, [], 1))
        self.assertEqual(1, dict_nested_get({'test': 'value'}, ['unknown'], 1))
        self.assertEqual(1, dict_nested_get({'test1': {'test2': 'value'}}, ['unknown'], 1))

    def test_dict_nested_get_value(self):
        """
        Tests dict_nested_get with a dictionary.
        """
        self.assertEqual('value', dict_nested_get({'test': 'value'}, ['test']))
        self.assertEqual('value', dict_nested_get({'test1': {'test2': 'value'}}, ['test1', 'test2']))
        self.assertEqual({'key': 'value'}, dict_nested_get({'test1': {'test2': {'key': 'value'}}}, ['test1', 'test2']))

    def test_json_default(self):
        """
        Tests json_default.
        """
        raw_time = time(10, 45)
        self.assertEqual(raw_time.isoformat(), json_default(raw_time))

        raw_date = date.today()
        self.assertEqual(raw_date.isoformat(), json_default(raw_date))

        raw_datetime = datetime.now()
        self.assertEqual(raw_datetime.astimezone(timezone.utc).isoformat(), json_default(raw_datetime))

        tz_datetime = datetime.now(timezone.utc)
        self.assertEqual(tz_datetime.isoformat(), json_default(tz_datetime))

        pytz_datetime = datetime.now(pytz.timezone('US/Eastern'))
        self.assertEqual(pytz_datetime.isoformat(), json_default(pytz_datetime))

        int_number = 1
        self.assertEqual(str(int_number), json_default(int_number))

        float_number = 1.23456
        self.assertEqual(str(float_number), json_default(float_number))

        decimal_number = Decimal(str(1.23456))
        self.assertEqual(float(decimal_number), json_default(decimal_number))

        dictionary = {'tz_datetime': tz_datetime, 'int_number': int_number, 'float_number': float_number, 'decimal_number': decimal_number}
        self.assertEqual(str(dictionary), json_default(dictionary))
        self.assertEqual(dictionary, json_default(MappingProxyType(dictionary)))

    def test_string_blank(self):
        """
        Tests string_blank.
        """
        self.assertTrue(string_blank(None))
        self.assertTrue(string_blank(''))
        self.assertTrue(string_blank(' '))
        self.assertFalse(string_blank('test'))
        self.assertFalse(string_blank(' test '))

    def test_string_camel_to_underscore(self):
        """
        Tests string_camel_to_underscore.
        """
        self.assertIsNone(string_camel_to_underscore(None))
        self.assertEqual('', string_camel_to_underscore(''))
        self.assertEqual('test', string_camel_to_underscore('test'))
        self.assertEqual('test_test', string_camel_to_underscore('TestTest'))

    def test_value_from_read_only(self):
        """
        Tests value_to_read_only.
        """
        value = MappingProxyType({'test': (1, 2, 3)})
        writable = value_from_read_only(value)
        self.assertIsNotNone(writable)
        self.assertEqual({'test': [1, 2, 3]}, writable)

        writable['test'] = [4, 5, 6]

        with pytest.raises(ValueError):
            writable['test'].remove(1)

        writable['test'].remove(4)

    def test_value_to_read_only(self):
        """
        Tests value_to_read_only.
        """
        value = {'test': [1, 2, 3]}
        read_only = value_to_read_only(value)
        self.assertIsNotNone(read_only)
        self.assertEqual(MappingProxyType({'test': (1, 2, 3)}), read_only)

        with pytest.raises(TypeError):
            read_only['test'] = [4, 5, 6]

        with pytest.raises(AttributeError):
            read_only['test'].remove(1)

    def test_value_to_string(self):
        """
        Tests value_to_string.
        """
        raw_time = time(10, 45)
        self.assertEqual(raw_time.isoformat(), value_to_string(raw_time))

        raw_date = date.today()
        self.assertEqual(raw_date.isoformat(), value_to_string(raw_date))

        raw_datetime = datetime.now()
        self.assertEqual(raw_datetime.astimezone(timezone.utc).isoformat(), value_to_string(raw_datetime))

        tz_datetime = datetime.now(timezone.utc)
        self.assertEqual(tz_datetime.isoformat(), value_to_string(tz_datetime))

        pytz_datetime = datetime.now(pytz.timezone('US/Eastern'))
        self.assertEqual(pytz_datetime.isoformat(), value_to_string(pytz_datetime))

        int_number = 1
        self.assertEqual(str(int_number), value_to_string(int_number))

        float_number = 1.23456
        self.assertEqual(str(float_number), value_to_string(float_number))

        decimal_number = Decimal(str(1.23456))
        self.assertEqual(str(decimal_number), value_to_string(decimal_number))

        dictionary = {'tz_datetime': tz_datetime, 'int_number': int_number, 'float_number': float_number, 'decimal_number': decimal_number}
        self.assertEqual(f"{{tz_datetime: {tz_datetime.isoformat()}, int_number: {int_number}, float_number: {float_number}, decimal_number: {decimal_number}}}",
                         value_to_string(dictionary))

        ordered_dictionary = OrderedDict(dictionary)
        self.assertEqual(f"{{tz_datetime: {tz_datetime.isoformat()}, int_number: {int_number}, float_number: {float_number}, decimal_number: {decimal_number}}}",
                         value_to_string(ordered_dictionary))
