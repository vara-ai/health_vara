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
        context = super().get_context(records, header, data)

        imaging_result = records[0].imaging_test_results[0]
        findings = imaging_result.findings
        mammography_findings = [
            f for f in findings if f.method == 'mammography']
        ultrasound_findings = [
            f for f in findings if f.method == 'ultrasound']

        context['imaging_result'] = imaging_result
        context['has_mammography_findings'] = len(mammography_findings) != 0
        context['has_ultrasound_findings'] = len(ultrasound_findings) != 0
        context['today'] = Date.today()

        return context
