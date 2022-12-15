# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from datetime import datetime

import pytz

from dateutil.relativedelta import relativedelta

from trytond.i18n import gettext
from trytond.model import ModelSingleton, ModelSQL, ModelView, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class MammographyPatient(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient'


    doc_referral = fields.Binary("Doctor's referral")
    image_acquisition_date = fields.DateTime("Image Acquisition Date",
        readonly=True)
    assessment_date = fields.DateTime("Assessment Date", readonly=True)
