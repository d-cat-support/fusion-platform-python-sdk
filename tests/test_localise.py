#
# Localise test file.
#
# @author Matthew Casey
#
# (c) Digital Content Analysis Technology Ltd 2022
#

import i18n

from tests.custom_test_case import CustomTestCase

from fusion_platform.localise import Localise


class TestLocalise(CustomTestCase):
    """
    Localise tests.
    """

    def test_setup(self):
        """
        Test setup to ensure no exceptions are raised and that the localisations are loaded.
        """
        Localise.setup()
        self.assertEqual(Localise._FALLBACK_LOCALE, i18n.get('fallback'))
        self.assertTrue(i18n.get('error_on_missing_translation'))
        self.assertTrue(i18n.get('error_on_missing_placeholder'))
        self.assertTrue(i18n.get('error_on_missing_plural'))
        self.assertTrue(i18n.get('enable_memoization'))

        self.assertEqual('Fusion Platform(r) SDK', i18n.t('fusion_platform.sdk'))

    def test_set_locale(self):
        """
        Test set locale to ensure that the locale is changed.
        """
        Localise.setup()
        self.assertEqual(Localise._FALLBACK_LOCALE, i18n.get('locale'))

        Localise.set_locale('ja_JP')
        self.assertEqual('ja_JP', i18n.get('locale'))
