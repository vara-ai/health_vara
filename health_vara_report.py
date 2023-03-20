# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.report import Report

__all__ = ['VaraFindingsReport']


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
        context['finding_details'] = finding_details

        return context
