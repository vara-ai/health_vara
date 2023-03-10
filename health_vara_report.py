# SPDX-FileCopyrightText: 2008-2023 Luis Falcón <falcon@gnuhealth.org>
# SPDX-FileCopyrightText: 2011-2023 GNU Solidario <health@gnusolidario.org>
#
# SPDX-License-Identifier: GPL-3.0-or-later

#########################################################################
#   Hospital Management Information System (HMIS) component of the      #
#                       GNU Health project                              #
#                   https://www.gnuhealth.org                           #
#########################################################################
#                           HEALTH package                              #
#   health_report.py: Disease, Medication and Vaccination reports       #
#########################################################################
import pytz
from datetime import datetime
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.report import Report

__all__ = ['VaraFindingsReport']


def get_print_date():
    Company = Pool().get('company.company')

    timezone = None
    company_id = Transaction().context.get('company')
    if company_id:
        company = Company(company_id)
        if company.timezone:
            timezone = pytz.timezone(company.timezone)

    dt = datetime.now()
    return datetime.astimezone(dt.replace(tzinfo=pytz.utc), timezone)


class VaraFindingsReport(Report):
    __name__ = 'patient.vara.findings'

    @classmethod
    def execute(cls, ids, data):
        with Transaction().set_context(address_with_party=True):
            return super().execute(ids, data)

    @classmethod
    def get_context(cls, records, header, data):
        pool = Pool()
        Date = pool.get('ir.date')
        Patient = pool.get('gnuhealth.patient')
        Company = pool.get('company.company')

        context = super().get_context(records, header, data)

        #print(cls, records, header, data)
        company_id = Transaction().context.get('company')
        report_address = ''
        if company_id:
            company = Company(company_id)
            address = company.party.addresses[0].full_address
            report_address = address.replace('\n', ', ')
            #report_address = ', '.join([_f for _f in [
            #        company.name,
            #        address.name,
            #        postal_code_city,
            #        self.street,
            #        country] if _f])
        context['company'] = company
        context['report_address'] = report_address
        context['today'] = Date.today()
        context['print_date'] = get_print_date()
        context['print_time'] = context['print_date'].time()
        #print(context)

        return context
