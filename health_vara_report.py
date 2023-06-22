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

        # get values for current imaging result
        current_imaging_result = None
        img_result_findings = []
        img_result_assessment = None
        img_result_density = None
        if len(imaging_results) != 0:
            current_imaging_result = imaging_results[0]
            img_result_findings = list(current_imaging_result.findings)
            img_result_density = current_imaging_result.density
            img_result_assessment = current_imaging_result.assessment

        # FIXME other findings is probably wrong, we currently look at all findings, but should have a way to look at
        # all findings related to the current study. I don't see how we'd link these other than by a guess on a date
        # range sadly. For now we do nothing since no system is very old!
        # https://app.asana.com/0/1201610932007292/1204823954787156
        imaging_finding_ids = set(map(lambda f: f.id, img_result_findings))
        other_findings = list(filter(lambda f: f.id not in imaging_finding_ids,
                                     patient.findings))
        all_findings = sorted([] + other_findings + img_result_findings,
                              key=lambda f: f.create_date, reverse=True)
        last_finding = all_findings[0] if all_findings else None

        # pick most recent non-null density
        all_densities = [img_result_density] + list(map(lambda f: _finding_density(f), all_findings))
        density = next(iter(filter(bool, all_densities)), None)

        # pick most severe assessment
        all_assessments = [img_result_assessment] + list(map(lambda f: f.bi_rads, all_findings))
        assessment = next(iter(sorted(filter(bool, all_assessments),
                                      key=lambda a: _SORTED_BIRADS.index(a.code),
                                      reverse=True)), None)

        has_ultrasound_finding = False
        for finding in all_findings:
            if finding.method == "ultrasound":
                has_ultrasound_finding = True
                break

        context['today'] = Date.today()
        context['has_ultrasound_findings'] = has_ultrasound_finding
        context["findings"] = all_findings
        context["density"] = density
        context["assessment"] = assessment
        context["imaging_result"] = current_imaging_result
        context["assessment_date"] = ((current_imaging_result and current_imaging_result.assessment_date)
                                      or
                                      (last_finding and last_finding.create_date))
        context["doctor"] = ((current_imaging_result and current_imaging_result.doctor)
                             or
                             (last_finding and last_finding.evaluated_by))
        return context
