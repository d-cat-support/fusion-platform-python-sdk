#
# Fields test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import ipaddress
from marshmallow import Schema
import uuid

from tests.custom_test_case import CustomTestCase

from fusion_platform.models import fields


class TestFields(CustomTestCase):
    class DummyModel():
        class DummyNestedSchema(Schema):
            nested = fields.String()

        boolean_field = True
        datetime_field = datetime.now(timezone.utc)
        decimal_field = 1.5
        dict_field = {'key': 'value'}
        email_field = 'test@d-cat.co.uk'
        float_field = 12.34
        integer_field = 10
        ipv4_field = ipaddress.ip_address('1.2.3.4')
        ipv6_field = ipaddress.ip_address('2a01:4b00:ea39:2700:24d8:8979:cddf:7bef')
        list_field = ['1', '2']
        nested_field = {'nested': 'test'}
        nested_list_field = [{'nested': '1'}, {'nested': '2'}]
        relativedelta_field = relativedelta(months=1)
        string_field = 'test'
        timedelta_field = timedelta(minutes=10)
        tuple_field = (1, 2)
        url_field = 'https://www.d-cat.co.uk/home'
        uuid_field = uuid.uuid4()

    def test_boolean(self):
        field = fields.Boolean()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('boolean_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.boolean_field)

    def test_datetime(self):
        field = fields.DateTime()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('datetime_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized.astimezone(timezone.utc), model.datetime_field.astimezone(timezone.utc))

    def test_decimal(self):
        field = fields.Decimal()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('decimal_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.decimal_field)

    def test_dict(self):
        field = fields.Dict()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('dict_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.dict_field)

    def test_email(self):
        field = fields.Email()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('email_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.email_field)

    def test_float(self):
        field = fields.Float()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('float_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.float_field)

    def test_integer(self):
        field = fields.Integer()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('integer_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.integer_field)

    def test_ip(self):
        field = fields.IP()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('ipv4_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.ipv4_field)

        serialized = field.serialize('ipv6_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.ipv6_field)

    def test_list(self):
        field = fields.List(fields.String())
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('list_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.list_field)

    def test_nested(self):
        field = fields.Nested(TestFields.DummyModel.DummyNestedSchema())
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('nested_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.nested_field)

    def test_nested_list(self):
        field = fields.List(fields.Nested(TestFields.DummyModel.DummyNestedSchema()))
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('nested_list_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.nested_list_field)

    def test_relativedelta(self):
        field = fields.RelativeDelta()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('relativedelta_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.relativedelta_field)

    def test_string(self):
        field = fields.String()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('string_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.string_field)

    def test_timedelta(self):
        field = fields.TimeDelta()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('timedelta_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.timedelta_field)

    def test_tuple(self):
        field = fields.Tuple((fields.Decimal(), fields.Decimal()))
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('tuple_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.tuple_field)

    def test_url(self):
        field = fields.Url()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('url_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.url_field)

    def test_uuid(self):
        field = fields.UUID()
        self.assertIsNotNone(field)

        model = TestFields.DummyModel()
        serialized = field.serialize('uuid_field', model)
        deserialized = field.deserialize(serialized)
        self.assertEqual(deserialized, model.uuid_field)
