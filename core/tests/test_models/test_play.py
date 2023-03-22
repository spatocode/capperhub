from django.test import TestCase
from core.models.play import Play, PlaySlip

class PlayModelTestCase(TestCase):
    fixtures = ['useraccount.json', 'users.json', 'pricing.json', 'currency.json', 'wallet.json', 'playslip.json', 'play.json']

    def test_slip_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("slip").verbose_name
        self.assertEqual(field_label, "slip")

    def test_status_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("status").verbose_name
        self.assertEqual(field_label, "status")

    def test_sports_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("sports").verbose_name
        self.assertEqual(field_label, "sports")

    def test_competition_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("competition").verbose_name
        self.assertEqual(field_label, "competition")

    def test_prediction_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("prediction").verbose_name
        self.assertEqual(field_label, "prediction")

    def test_home_team_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("home_team").verbose_name
        self.assertEqual(field_label, "home team")

    def test_away_team_label(self):
        play = Play.objects.get(id=82)
        field_label = play._meta.get_field("away_team").verbose_name
        self.assertEqual(field_label, "away team")

    def test__str__label(self):
        play = Play.objects.get(id=82)
        self.assertEqual(play.__str__(), f"{play.sports}-{play.slip.issuer.user.username}")


class PlaySlipModelTestCase(TestCase):
    fixtures = ['playslip.json', 'useraccount.json', 'users.json', 'pricing.json', 'currency.json', 'wallet.json']

    def test_title_label(self):
        play_slip = PlaySlip.objects.get(id=35)
        field_label = play_slip._meta.get_field("title").verbose_name
        self.assertEqual(field_label, "title")

    def test_issuer_label(self):
        play_slip = PlaySlip.objects.get(id=35)
        field_label = play_slip._meta.get_field("issuer").verbose_name
        self.assertEqual(field_label, "issuer")

    def test_date_added_label(self):
        play_slip = PlaySlip.objects.get(id=35)
        field_label = play_slip._meta.get_field("date_added").verbose_name
        self.assertEqual(field_label, "date added")

    def test_is_premium_label(self):
        play_slip = PlaySlip.objects.get(id=35)
        field_label = play_slip._meta.get_field("is_premium").verbose_name
        self.assertEqual(field_label, "is premium")
