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

        # Note: `records` should always be a singleton list.
        assert (len(records) == 1)
        patient = records[0]

        # Sort imaging test results for each patient ID in reverse chronological
        # order. We need the most recent imaging results recorded for a patient.
        imaging_results = sorted(patient.imaging_test_results,
                                key=lambda r: r.create_date,
                                reverse=True)
        context['today'] = Date.today()
        if len(imaging_results) != 0:
            findings = imaging_results[0].findings
            mammography_findings = [
                f for f in findings if f.method == 'mammography']
            ultrasound_findings = [
                f for f in findings if f.method == 'ultrasound']
            context['imaging_result'] = imaging_results[0]
            context['has_mammography_findings'] = len(
                mammography_findings) != 0
            context['has_ultrasound_findings'] = len(ultrasound_findings) != 0

        return context
