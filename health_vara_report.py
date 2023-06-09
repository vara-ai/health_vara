# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from collections import defaultdict

from trytond.pool import Pool
from trytond.report import Report
from trytond.transaction import Transaction

__all__ = ['VaraFindingsReport']


_SORTED_BIRADS = ["0", "1", "2", "3", "4A", "4B", "4C", "5", "6"]


def _finding_density(finding):
    if finding.method == "mammography":
        return {"fatty": "A", "scattered": "B", "heterogeneous": "C",
                "extreme": "D"}.get(finding.mammo_composition, None)

    if finding.method == "ultrasound":
        return {"fat": "A", "fibroglandular": "B", "heterogeneous": "C"}.get(
            finding.ultrasound_tissue_composition, None)


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
        context['has_ultrasound_findings'] = False

        findings = []
        imaging_result = None
        assessment = None
        density = None
        last_finding = None

        # Processing findings associated with the latest Imaging Result.
        if len(imaging_results) != 0:
            imaging_result = imaging_results[0]
            findings = findings + list(imaging_result.findings)
            density = imaging_result.density
            assessment = imaging_result.assessment

        # Processing findings outside the imaging results workflow.
        imaging_finding_ids = set(map(lambda f: f.id, findings))
        other_findings = list(filter(lambda f: f.id not in imaging_finding_ids,
                                     patient.findings))
        findings = findings + other_findings

        if imaging_result and imaging_result.density:
            density = imaging_result.density
        elif other_findings:
            last_finding = sorted(
                other_findings, key=lambda f: f.create_date, reverse=True)[0]
            density = _finding_density(last_finding)

        if not assessment and findings:
            findings_with_birads = filter(lambda f: f.bi_rads, findings)
            if findings_with_birads:
                assessment = max(
                    findings_with_birads, key=lambda f: _SORTED_BIRADS.index(f.bi_rads.code)).bi_rads

        for finding in findings:
            if finding.method == "ultrasound":
                context["has_ultrasound_findings"] = True
                break

        context["findings"] = findings
        context["last_finding"] = last_finding
        context["density"] = density
        context["assessment"] = assessment
        context["imaging_result"] = imaging_result
        context["assessment_date"] = (
            imaging_result and imaging_result.assessment_date) or (last_finding and last_finding.create_date)
        context["doctor"] = (imaging_result and imaging_result.doctor) or (
            last_finding and last_finding.evaluated_by)
        return context
