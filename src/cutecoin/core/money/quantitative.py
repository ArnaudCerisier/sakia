from PyQt5.QtCore import QCoreApplication, QT_TRANSLATE_NOOP, QObject, QLocale


class Quantitative():
    _NAME_STR_ = QT_TRANSLATE_NOOP('Quantitative', 'Units')
    _REF_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0} {1}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Quantitative', "{0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Quantitative', Quantitative._NAME_STR_)

    @classmethod
    def units(cls, currency):
        return QCoreApplication.translate("Quantitative", Quantitative._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(cls, currency):
        return Quantitative.units(currency)

    def value(self):
        """
        Return quantitative value of amount

        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: int
        """
        return int(self.amount)

    def differential(self):
        return self.value()

    def _to_si(self, value):
        prefixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'z', 'y']
        scientific_value = value
        prefix_index = 0
        prefix = ""

        while scientific_value > 1000:
            prefix_index += 1
            scientific_value /= 1000

        if prefix_index < len(prefixes):
            prefix = prefixes[prefix_index]
            localized_value = QLocale().toString(float(scientific_value), 'f', 3)
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        return localized_value, prefix

    def localized(self, units=False, international_system=False):
        value = self.value()
        prefix = ""
        if international_system:
            localized_value, prefix = self._to_si(value)
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = self.differential()
        prefix = ""
        if international_system:
            localized_value, prefix = self._to_si(value)
        else:
            localized_value = QLocale().toString(float(value), 'f', 0)

        if units or international_system:
            return QCoreApplication.translate("Quantitative",
                                              Quantitative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value
