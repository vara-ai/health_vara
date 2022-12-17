# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool

from . import health_vara
from . import health_imaging

__all__ = ['register']


def register():
    Pool.register(
        health_vara.MammographyPatient,
        health_vara.PatientEvaluation,
        health_imaging.ImagingTestResult,
        health_imaging.ImagingFinding,
        module='health_vara', type_='model')
    Pool.register(
        module='health_vara', type_='wizard')
    Pool.register(
        module='health_vara', type_='report')
