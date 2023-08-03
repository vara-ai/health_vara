# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool

from . import health_vara
from . import health_imaging
from . import health_vara_report

__all__ = ['register']


def register():
    Pool.register(
        health_vara.Party,
        health_vara.MammographyPatient,
        health_vara.PatientEvaluation,
        health_imaging.ImagingTestRequest,
        health_imaging.ImagingTestResult,
        health_imaging.ImagingFinding,
        health_imaging.BIRADS,
        health_imaging.RequestPatientImagingTestStart,
        module='health_vara', type_='model')
    Pool.register(
        health_imaging.RequestPatientImagingTestOverride,
        module='health_vara', type_='wizard')
    Pool.register(
        health_vara_report.VaraFindingsReport,
        module='health_vara', type_='report')
