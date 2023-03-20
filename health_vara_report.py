# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from collections import defaultdict

from trytond.pool import Pool
from trytond.report import Report
from trytond.transaction import Transaction

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
        Finding = pool.get('gnuhealth.imaging.finding')
        Company = pool.get('company.company')
        IrLang = pool.get('ir.lang')

        context = super().get_context(records, header, data)

        #print(cls, records, header, data)
        company_id = Transaction().context.get('company')
        report_address = ''
        if company_id:
            company = Company(company_id)
            address = company.party.addresses[0].full_address
            report_address = address.replace('\n', ', ')

        def format_label(label):
            # Format the label for printout and put a separator for parsing
            # inside the report
            label += ':'
            return label + ' |'

        # Define the fields to be searched for details
        detail_types = {'mammo_', 'ultrasound_', 'mri_'}
        detail_fields = []
        for field in Finding._fields:
            for type in detail_types:
                if field.startswith(type) and not field.endswith('_string'):
                    detail_fields.append(field)

        # Find detail fields with content and create a parsable dict of
        # field labels and values
        finding_details = defaultdict(int)
        lang = IrLang.get()
        for patient in records:
            for finding in patient.findings:
                fields_with_content = [field for field in finding._fields
                    if getattr(finding, field, None)
                    and field in detail_fields]
                if fields_with_content:
                    item = 0
                    finding_details[finding.id] = ''
                    for field in fields_with_content:
                        field_def = finding._fields[field].definition(
                            finding, lang.code)
                        # TODO: translate values
                        value = getattr(finding, field, None)
                        if field_def['type'] == 'boolean':
                            if value:
                                value = 'Yes'
                            else:
                                value = 'No'
                        if item > 0:
                            finding_details[finding.id] += '\n'
                        label = format_label(field_def['string'])
                        finding_details[finding.id] += '%s%s' % (label,
                            value.capitalize())
                        item += 1

        context['company'] = company
        context['report_address'] = report_address
        context['today'] = Date.today()
        context['finding_details'] = finding_details

        return context
