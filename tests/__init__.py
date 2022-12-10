# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

try:
    from trytond.modules.health_vara.tests.test_health_vara import suite  # noqa: E501, isort: skip
except ImportError:
    from .test_health_vara import suite

__all__ = ['suite']
