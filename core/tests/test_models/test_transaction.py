from django.test import TestCase
from django.contrib.auth.models import User
from core.models.transaction import Transaction, Currency


class TransactionModelTestCase(TestCase):
    fixtures = ['transaction.json', 'currency.json', 'useraccount.json', 'users.json', 'pricing.json', 'wallet.json']

    def test_type_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("type").verbose_name
        self.assertEqual(field_label, "type")

    def test_amount_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("amount").verbose_name
        self.assertEqual(field_label, "amount")

    def test_balance_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("balance").verbose_name
        self.assertEqual(field_label, "balance")

    def test_reference_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("reference").verbose_name
        self.assertEqual(field_label, "reference")

    def test_payment_issuer_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("payment_issuer").verbose_name
        self.assertEqual(field_label, "payment issuer")

    def test_channel_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("channel").verbose_name
        self.assertEqual(field_label, "channel")

    def test_status_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("status").verbose_name
        self.assertEqual(field_label, "status")

    def test_user_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("user").verbose_name
        self.assertEqual(field_label, "user")

    def test_currency_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("currency").verbose_name
        self.assertEqual(field_label, "currency")

    def test_time_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("time").verbose_name
        self.assertEqual(field_label, "time")

    def test_last_update_label(self):
        transaction = Transaction.objects.get(id=51)
        field_label = transaction._meta.get_field("last_update").verbose_name
        self.assertEqual(field_label, "last update")


class CurrencyModelTestCase(TestCase):
    fixtures = ['currency.json']

    def test_code_label(self):
        currency = Currency.objects.get(code="USD")
        field_label = currency._meta.get_field("code").verbose_name
        self.assertEqual(field_label, "code")

    def test_country_label(self):
        currency = Currency.objects.get(code="USD")
        field_label = currency._meta.get_field("country").verbose_name
        self.assertEqual(field_label, "country")

    def test__str__label(self):
        currency = Currency.objects.get(code="USD")
        self.assertEqual(currency.__str__(), f"{currency.code}")
