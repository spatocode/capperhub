from django.contrib.auth.models import User
from django.test import TestCase
from core.models.user import UserAccount, Wallet, Pricing
from core.models.transaction import Currency


#TODO: Add model property tests
class UserAccountModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(username="johndoe", password="password")

    def test_display_name_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("display_name").verbose_name
        self.assertEqual(field_label, "display name")

    def test_bio_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("bio").verbose_name
        self.assertEqual(field_label, "bio")

    def test_country_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("country").verbose_name
        self.assertEqual(field_label, "country")

    def test_phone_number_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("phone_number").verbose_name
        self.assertEqual(field_label, "phone number")

    def test_twitter_handle_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("twitter_handle").verbose_name
        self.assertEqual(field_label, "twitter handle")

    def test_instagram_handle_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("instagram_handle").verbose_name
        self.assertEqual(field_label, "instagram handle")

    def test_pricing_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("pricing").verbose_name
        self.assertEqual(field_label, "pricing")

    def test_wallet_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("wallet").verbose_name
        self.assertEqual(field_label, "wallet")

    def test_ip_address_label(self):
        user_account = UserAccount.objects.get(id=6)
        field_label = user_account._meta.get_field("ip_address").verbose_name
        self.assertEqual(field_label, "ip address")
    
    def test__str__(self):
        user_account = UserAccount.objects.get(id=6)
        self.assertEqual(user_account.__str__(), f"{user_account.user.username}")
    
    def test_full_name_when_names_available(self):
        first_name = "Ekene"
        last_name = "Izukanne"
        user_account = UserAccount.objects.get(id=6)
        user_account.user.first_name = first_name
        user_account.user.last_name = last_name
        user_account.user.save()
        self.assertEqual(user_account.full_name, f"{user_account.user.first_name} {user_account.user.last_name}")
    
    def test_full_name_when_names_not_available(self):
        user_account = UserAccount.objects.get(id=6)
        user_account.user.first_name = ""
        user_account.user.last_name = ""
        user_account.user.save()
        self.assertEqual(user_account.full_name, "")


class WalletModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        currency = Currency.objects.create(code="NGN", country="NG")
        Wallet.objects.create(currency=currency)

    def test_currency_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("currency").verbose_name
        self.assertEqual(field_label, "currency")

    def test_balance_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("balance").verbose_name
        self.assertEqual(field_label, "balance")

    def test_withheld_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("withheld").verbose_name
        self.assertEqual(field_label, "withheld")

    def test_bank_name_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("bank_name").verbose_name
        self.assertEqual(field_label, "bank name")

    def test_bank_account_number_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("bank_account_number").verbose_name
        self.assertEqual(field_label, "bank account number")

    def test_authorizations_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("authorizations").verbose_name
        self.assertEqual(field_label, "authorizations")

    def test_receipient_code_label(self):
        wallet = Wallet.objects.get(id=1)
        field_label = wallet._meta.get_field("receipent_code").verbose_name
        self.assertEqual(field_label, "receipent code")

    def test__str__(self):
        wallet = Wallet.objects.get(id=1)
        self.assertEqual(wallet.__str__(), f"{wallet.balance} - {wallet.bank_name}")


class PricingModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        Pricing.objects.get_or_create(amount="1000")

    def test_amount_label(self):
        pricing = Pricing.objects.get(id=1)
        field_label = pricing._meta.get_field("amount").verbose_name
        self.assertEqual(field_label, "amount")

    def test_percentage_discount_label(self):
        pricing = Pricing.objects.get(id=1)
        field_label = pricing._meta.get_field("percentage_discount").verbose_name
        self.assertEqual(field_label, "percentage discount")

    def test_last_update_label(self):
        pricing = Pricing.objects.get(id=1)
        field_label = pricing._meta.get_field("last_update").verbose_name
        self.assertEqual(field_label, "last update")

    def test_free_features_label(self):
        pricing = Pricing.objects.get(id=1)
        field_label = pricing._meta.get_field("free_features").verbose_name
        self.assertEqual(field_label, "free features")

    def test_premium_features_label(self):
        pricing = Pricing.objects.get(id=1)
        field_label = pricing._meta.get_field("premium_features").verbose_name
        self.assertEqual(field_label, "premium features")

    def test__str__(self):
        pricing = Pricing.objects.get(id=1)
        self.assertEqual(pricing.__str__(), f"{pricing.amount}")
