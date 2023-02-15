# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.config import config
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta

if config.getboolean('health_vara', 'filestore', default=True):
    file_id = 'result_report_cache_id'
    store_prefix = config.get('health_vara', 'store_prefix', default=None)
else:
    file_id = None
    store_prefix = None


class ImagingTestResult(metaclass=PoolMeta):
    __name__ = 'gnuhealth.imaging.test.result'

    result_report_cache = fields.Binary('Imaging Result Report', readonly=True,
        file_id=file_id, store_prefix=store_prefix)
    result_report_cache_id = fields.Char('Result Report ID', readonly=True)
    result_report_format = fields.Char('Result Report Format', readonly=True)

    report_link = fields.Char("Report Download URL",
        help="Link to download the Vara report",
        readonly=True)

    prior_study_considered = fields.Boolean('Prior study considered',
            readonly=True)

    image_acquisition_date = fields.DateTime(
        'Image Acquisition Date', readonly=True)
    technical_quality_rcc = fields.Selection('get_quality_selection',
        'Technical Quality RCC', readonly=True)
    technical_quality_rmlo = fields.Selection('get_quality_selection',
        'Technical Quality RMLO', readonly=True)
    technical_quality_lcc = fields.Selection('get_quality_selection',
        'Technical Quality LCC', readonly=True)
    technical_quality_lmlo = fields.Selection('get_quality_selection',
        'Technical Quality LMLO', readonly=True)

    assessment_date = fields.DateTime('Assessment Date', readonly=True)
    clinical_recall = fields.Char('Clinical Recall', readonly=True)

    findings = fields.One2Many(
        'gnuhealth.imaging.finding', 'imaging_result', 'Findings')
    density = fields.Selection([
            (None, ''),
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D')],
        'Density', readonly=True)
    assessment = fields.Selection([
            (None, ''),
            ('0', '0'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4a', '4a'),
            ('4b', '4b'),
            ('4c', '4c'),
            ('5', '5'),
            ('6', '6')],
        'Assessment', readonly=True)

    @classmethod
    def get_quality_selection(cls):
        return [
            (None, ''),
            ('no_limitations', 'No Limitations'),
            ('restricted', 'Restricted'),
            ('repeat', 'Repeat'),
            ]


class ImagingFinding(ModelSQL, ModelView):
    'Imaging Test Result Finding'
    __name__ = 'gnuhealth.imaging.finding'

    imaging_result = fields.Many2One(
        'gnuhealth.imaging.test.result', 'Imaging Test Result', required=True,
        readonly=True)
    number = fields.Integer('Number', readonly=True)
    laterality = fields.Char('Laterality', readonly=True)
    localisation = fields.Char('Localisation', readonly=True)
    type = fields.Char('Type', readonly=True)
    size = fields.Char('Size', readonly=True)
    bi_rads = fields.Char('BI-RADS', readonly=True)
