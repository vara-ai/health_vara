# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.config import config
from trytond.model import ModelSQL, ModelView, fields
from trytond.modules.health.core import (
    compute_age_from_dates, get_health_professional)
from trytond.pool import PoolMeta
from trytond.pyson import Eval

if config.getboolean('health_vara', 'filestore', default=True):
    file_id = 'result_report_cache_id'
    store_prefix = config.get('health_vara', 'store_prefix', default=None)
else:
    file_id = None
    store_prefix = None


class ImagingTestResult(metaclass=PoolMeta):
    __name__ = 'gnuhealth.imaging.test.result'

    # Remove once https://savannah.gnu.org/bugs/?63842 is solved
    def patient_age_at_evaluation(self, name):
        if (self.patient and self.patient.name.dob and self.date):
            return compute_age_from_dates(
                self.patient.name.dob, None, None, None, 'age',
                self.date.date())

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
    assessment = fields.Many2One('gnuhealth.imaging.birads', 'Assessment',
        readonly=True)
    clinical_recall = fields.Char('Clinical Recall', readonly=True)
    findings = fields.One2Many('gnuhealth.imaging.finding', 'patient',
        'Findings', readonly=True)
    density = fields.Selection([
            (None, ''),
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D')],
        'Density', readonly=True)

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

    _ultrasound_states = {
            'invisible': (Eval('method') != 'ultrasound'),
            }
    _mammo_states = {
            'invisible': (Eval('method') != 'mammography'),
            }
    _mri_states = {
            'invisible': (Eval('method') != 'mri'),
            }

    patient = fields.Many2One('gnuhealth.patient', 'Patient',
        required=True)
    imaging_result = fields.Many2One(
        'gnuhealth.imaging.test.result', 'Imaging Test Result')
    finding_date = fields.DateTime('Date', required=True)
    number = fields.Integer('Number')
    method = fields.Selection([
            ('ultrasound', 'Ultrasound'),
            ('mammography', 'Mammography'),
            ('mri', 'MRI (Magnetic Resonance Imaging)'),
            ], 'Method', sort=False, required=True)
    method_string = method.translated('method')
    laterality = fields.Selection([
            ('left_breast', 'Left Breast'),
            ('right_breast', 'Right Breast'),
            ], 'Laterality', required=True)
    laterality_string = laterality.translated('laterality')
    localisation = fields.Char('Localisation')
    lesion_type = fields.Char('Lesion Type')
    size = fields.Integer('Size',
        help='Size in mm')
    bi_rads = fields.Many2One(
        'gnuhealth.imaging.birads', 'BI-RADS')
    bi_rads_comment = fields.Function(fields.Char('Comment'),
        'on_change_with_bi_rads_comment')
    biopsy_recommendation = fields.Selection([
            (None, ''),
            ('suspicious', 'Suspicious, should be biopsied'),
            ('not_suspicious', 'Not suspicious (FP)'),
            ],
        'Biopsy Recommendation')
    biopsy_recommendation_string = biopsy_recommendation.translated(
        'biopsy_recommendation')
    comment = fields.Text('Comment')
    evaluated_by = fields.Many2One(
        'gnuhealth.healthprofessional', 'Evaluated by', required=True)

    # Ultrasound
    ultrasound_tissue_composition = fields.Selection([
            (None, ''),
            ('fat', 'homogeneous background echotexture - fat'),
            ('fibroglandular',
                'homogeneous background echotexture - fibroglandular'),
            ('heterogeneous', 'heterogeneous background echotexture'),
            ], 'Tissue Composition', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_tissue_composition_string = (
        ultrasound_tissue_composition.translated(
            'ultrasound_tissue_composition'))
    ultrasound_masses_shape = fields.Selection([
            (None, ''),
            ('oval', 'oval'),
            ('round', 'round'),
            ('irregular', 'irregular'),
            ], 'Shape', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_masses_orientation = fields.Selection([
            (None, ''),
            ('parallel', 'parallel'),
            ('not_parallel', 'not parallel'),
            ], 'Orientation', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_masses_margin = fields.Selection([
            (None, ''),
            ('circumscribed', 'circumscribed'),
            ('angular', 'angular'),
            ('microlobulated', 'microlobulated'),
            ('indistinct', 'indistinct'),
            ('spiculated', 'spiculated'),
            ], 'Margin', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_masses_echo_pattern = fields.Selection([
            (None, ''),
            ('anechoic', 'anechoic'),
            ('hyperechoic', 'hyperechoic'),
            ('hypoechoic', 'hypoechoic'),
            ('isoechoic', 'isoechoic'),
            ('heterogeneous', 'heterogeneous'),
            ('complex', 'complex cystic and solid'),
            ], 'Echo Pattern (in comparison to subcutaneous fat)',
        sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_masses_posterior_features = fields.Selection([
            (None, ''),
            ('no posterior features', 'no posterior features'),
            ('enhancement', 'enhancement'),
            ('shadowing', 'shadowing'),
            ('combined', 'combined pattern'),
            ], 'Posterior Features', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_calcifications_in_mass = fields.Boolean(
        'Calcifications in a mass',
        states=_ultrasound_states, depends=['method'])
    ultrasound_calcifications_outside_mass = fields.Boolean(
        'Calcifications outside of a mass',
        states=_ultrasound_states, depends=['method'])
    ultrasound_calcifications_intraductal = fields.Boolean(
        'Intraductal calcifications',
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_architectural_distortion = fields.Boolean(
        'Architectural distortion',
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_duct_changes = fields.Boolean(
        'Duct changes',
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_skin_changes = fields.Selection([
            (None, ''),
            ('thickening', 'Skin thickening'),
            ('retractions', 'Skin retractions'),
            ], 'Skin changes', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_skin_changes_string = (
        ultrasound_associated_skin_changes.translated(
            'ultrasound_associated_skin_changes'))
    ultrasound_associated_edema = fields.Boolean(
        'Edema',
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_vascularity = fields.Selection([
            (None, ''),
            ('absent', 'Absent'),
            ('internal', 'Internal vascularity'),
            ('rim', 'Vessels in rim'),
            ], 'Vascularity', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_associated_elasticity = fields.Selection([
            (None, ''),
            ('soft', 'soft'),
            ('intermediate', 'intermediate'),
            ('hard', 'hard'),
            ], 'Elasticity assessment', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_simple_cyst = fields.Boolean(
        'Simple cyst',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_clustered_microcysts = fields.Boolean(
        'Clustered microcysts',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_complicated_cyst = fields.Boolean(
        'Complicated cyst',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_mass_in_or_on_skin = fields.Boolean(
        'Mass in or on skin',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_foreign_body = fields.Boolean(
        'Foreign body including implants',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_intramammary_lymph_nodes = fields.Boolean(
        'Intramammary lymph nodes',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_axillary_lymph_nodes = fields.Boolean(
        'Axillary lymph nodes',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_vascular = fields.Selection([
            (None, ''),
            ('malformations', 'Arteriovenous malformations/pseudoaneurysms'),
            ('mondor', 'Mondor disease'),
            ], 'Vascular abnormalities', sort=False,
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_postsurgical_fluid = fields.Boolean(
        'Postsurgical fluid collection',
        states=_ultrasound_states, depends=['method'])
    ultrasound_special_fat_necrosis = fields.Boolean(
        'Fat necrosis',
        states=_ultrasound_states, depends=['method'])

    # Mammography
    mammo_composition = fields.Selection([
            (None, ''),
            ('fatty', 'fatty: the breasts are almost entirely fatty'),
            ('scattered', 'scattered fibroglandular: '
                'there are scattered areas of fibroglandular density'),
            ('heterogeneous', 'heterogeneously dense: '
                'the breasts are heterogeneously dense, which may '
                'obscure small masses'),
            ('extreme:', 'extremely dense: '
                'the breasts are extremely dense, which lowers '
                'the sensitivity of mammography'),
            ], 'Breast Composition', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_masses_shape = fields.Selection([
            (None, ''),
            ('oval', 'oval'),
            ('round', 'round'),
            ('irregular', 'irregular'),
            ], 'Shape', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_masses_margin = fields.Selection([
            (None, ''),
            ('circumscribed', 'circumscribed'),
            ('obscured', 'obscured'),
            ('microlobulated', 'microlobulated'),
            ('indistinct', 'indistinct'),
            ('spiculated', 'spiculated'),
            ], 'Margin', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_density = fields.Selection([
            (None, ''),
            ('high', 'high density'),
            ('equal', 'equal density'),
            ('low', 'low density'),
            ('fat', 'fat-containing'),
            ], 'Density', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_calcifications_benign = fields.Selection([
            (None, ''),
            ('skin', 'skin'),
            ('vascular', 'vascular'),
            ('coarse', 'coarse or "popcorn-like"'),
            ('large', 'large rod-like'),
            ('round', 'round'),
            ('rim', 'rim'),
            ('dystrophic', 'dystrophic'),
            ('milk', 'milk of calcium'),
            ('suture', 'suture'),
            ], 'Typically benign', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_calcifications_suspicious = fields.Selection([
            (None, ''),
            ('amorphous', 'amorphous'),
            ('coarse', 'coarse heterogeneous'),
            ('fine_pleomorphic', 'fine pleomorphic'),
            ('fine_linear', 'fine linear or fine-linear branching'),
            ], 'Suspicious morphology', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_calcifications_distribution = fields.Selection([
            (None, ''),
            ('diffuse', 'diffuse'),
            ('regional', 'regional'),
            ('grouped', 'grouped'),
            ('linear', 'linear'),
            ('segmental', 'segmental'),
            ], 'Distribution', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_other_architectural_distortion = fields.Boolean(
        'Architectural distortion',
        states=_mammo_states, depends=['method'])
    mammo_other_asymmetries = fields.Selection([
            (None, ''),
            ('asymmetry', 'asymmetry'),
            ('focal', 'focal asymmetry'),
            ('developing', 'developing asymmetry'),
            ('global', 'global asymmetry'),
            ], 'Asymmetries', sort=False,
        states=_mammo_states, depends=['method'])
    mammo_other_intramammary_lymph_node = fields.Boolean(
        'Intramammary lymph node',
        states=_mammo_states, depends=['method'])
    mammo_other_skin_lesion = fields.Boolean(
        'Skin lesion',
        states=_mammo_states, depends=['method'])
    mammo_other_solitary_duct = fields.Boolean(
        'Solitary dilated duct',
        states=_mammo_states, depends=['method'])
    mammo_associated_skin_retraction = fields.Boolean(
        'Skin retraction',
        states=_mammo_states, depends=['method'])
    mammo_associated_nipple_retraction = fields.Boolean(
        'Nipple retraction',
        states=_mammo_states, depends=['method'])
    mammo_associated_skin_thickening = fields.Boolean(
        'Skin thickening',
        states=_mammo_states, depends=['method'])
    mammo_associated_trabecular_thickening = fields.Boolean(
        'Trabecular thickening',
        states=_mammo_states, depends=['method'])
    mammo_associated_axillary_adenopathy = fields.Boolean(
        'Axillary adenopathy',
        states=_mammo_states, depends=['method'])
    mammo_associated_architectural_distortion = fields.Boolean(
        'Architectural distortion',
        states=_mammo_states, depends=['method'])
    mammo_associated_calcifications = fields.Boolean(
        'Calcifications',
        states=_mammo_states, depends=['method'])

    # MRI
    mri_tissue = fields.Selection([
            (None, ''),
            ('fat', 'almost entirely fat'),
            ('scattered', 'scattered fibroglandular tissue'),
            ('heterogeneous', 'heterogeneous fibroglandular tissue'),
            ('extreme', 'extreme fibroglandular tissue'),
            ], 'Amount of fibroglandular tissue', sort=False,
        states=_mri_states, depends=['method'])
    mri_background_level = fields.Selection([
            (None, ''),
            ('minimal', 'minimal'),
            ('mild', 'mild'),
            ('moderate', 'moderate'),
            ('marked', 'marked'),
            ], 'Level', sort=False,
        states=_mri_states, depends=['method'])
    mri_background_symmetrie = fields.Selection([
            (None, ''),
            ('symmetric', 'symmetric'),
            ('asymmetric', 'asymmetric'),
            ], 'Symmetrie', sort=False,
        states=_mri_states, depends=['method'])
    mri_masses_shape = fields.Selection([
            (None, ''),
            ('oval', 'oval'),
            ('round', 'round'),
            ('irregular', 'irregular'),
            ], 'Shape', sort=False,
        states=_mri_states, depends=['method'])
    mri_masses_margin = fields.Selection([
            (None, ''),
            ('circumscribed', 'circumscribed'),
            ('irregular', 'irregular'),
            ('spiculated', 'spiculated'),
            ], 'Margin', sort=False,
        states=_mri_states, depends=['method'])
    mri_masses_internal_enhancement = fields.Selection([
            (None, ''),
            ('homogeneous', 'homogeneous'),
            ('heterogeneous', 'heterogeneous'),
            ('rim', 'rim enhancement'),
            ('dark', 'dark internal septations'),
            ], 'Internal enhancement characteristics', sort=False,
        states=_mri_states, depends=['method'])
    mri_non_mass_distribution = fields.Selection([
            (None, ''),
            ('focal', 'focal'),
            ('linear', 'linear'),
            ('segmental', 'segmental'),
            ('regional', 'regional'),
            ('multiple', 'multiple regions'),
            ('diffuse', 'diffuse'),
            ], 'Distribution', sort=False,
        states=_mri_states, depends=['method'])
    mri_non_mass_enhancement_patterns = fields.Selection([
            (None, ''),
            ('homogeneous', 'homogeneous'),
            ('heterogeneous', 'heterogeneous'),
            ('clumped', 'clumped'),
            ('clustered', 'clustered ring'),
            ], 'Internal enhancement patterns', sort=False,
        states=_mri_states, depends=['method'])
    mri_other_focus = fields.Boolean(
        'Focus',
        states=_mri_states, depends=['method'])
    mri_other_intramammary_lymph_node = fields.Boolean(
        'Intramammary lymph node',
        states=_mri_states, depends=['method'])
    mri_other_skin_lesion = fields.Boolean(
        'Skin lesion',
        states=_mri_states, depends=['method'])
    mri_other_ductal_precontrast = fields.Boolean(
        'Ductal precontrast high signal on T1W',
        states=_mri_states, depends=['method'])
    mri_other_cyst = fields.Boolean(
        'Cyst',
        states=_mri_states, depends=['method'])
    mri_other_postoperative_collections = fields.Boolean(
        'Postoperative collections (hematoma/seroma)',
        states=_mri_states, depends=['method'])
    mri_other_post_therapy_thickening = fields.Boolean(
        'Post-therapy skin thickening and trabecular thickening',
        states=_mri_states, depends=['method'])
    mri_other_non_enhancing_mass = fields.Boolean(
        'Non-enhancing mass',
        states=_mri_states, depends=['method'])
    mri_other_architectural_distortion = fields.Boolean(
        'Architectural distortion',
        states=_mri_states, depends=['method'])
    mri_other_signal_void = fields.Boolean(
        'Signal void from foreign bodies, clips, etc.',
        states=_mri_states, depends=['method'])
    mri_associated_nipple_retraction = fields.Boolean(
        'Nipple retraction',
        states=_mri_states, depends=['method'])
    mri_associated_nipple_invasion = fields.Boolean(
        'Nipple invasion',
        states=_mri_states, depends=['method'])
    mri_associated_skin_retraction = fields.Boolean(
        'Skin retraction',
        states=_mri_states, depends=['method'])
    mri_associated_skin_thickening = fields.Boolean(
        'Skin thickening',
        states=_mri_states, depends=['method'])
    mri_associated_skin_invasion = fields.Selection([
            (None, ''),
            ('direct', 'direct invasion'),
            ('inflammatory', 'inflammatory cancer'),
            ], 'Skin invasion', sort=False,
        states=_mri_states, depends=['method'])
    mri_associated_axillary_adenopathy = fields.Boolean(
        'Axillary adenopathy',
        states=_mri_states, depends=['method'])
    mri_associated_pectoralis_invasion = fields.Boolean(
        'Pectoralis muscle invasion',
        states=_mri_states, depends=['method'])
    mri_associated_chest_invasion = fields.Boolean(
        'Chest wall invasion',
        states=_mri_states, depends=['method'])
    mri_associated_architectural_distortion = fields.Boolean(
        'Architectural distortion',
        states=_mri_states, depends=['method'])
    mri_fat_containing_lesions_lymph_nodes = fields.Selection([
            (None, ''),
            ('normal', 'normal'),
            ('abnormal', 'abnormal'),
            ], 'Lymph nodes', sort=False,
        states=_mri_states, depends=['method'])
    mri_fat_containing_lesions_fat_necrosis = fields.Boolean(
        'Fat necrosis',
        states=_mri_states, depends=['method'])
    mri_fat_containing_lesions_hamartoma = fields.Boolean(
        'Hamartoma',
        states=_mri_states, depends=['method'])
    mri_fat_containing_lesions_postoperative_seroma_hematoma = fields.Boolean(
        'Postoperative seroma/hematoma with fat',
        states=_mri_states, depends=['method'])
    mri_kinetic_curve_initial_phase = fields.Selection([
            (None, ''),
            ('slow', 'slow'),
            ('medium', 'medium'),
            ('fast', 'fast'),
            ], 'Initial phase', sort=False,
        states=_mri_states, depends=['method'])
    mri_kinetic_curve_delayed_phase = fields.Selection([
            (None, ''),
            ('persistent', 'persistent'),
            ('plateau', 'plateau'),
            ('washout', 'washout'),
            ], 'Delayed phase', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_implant_material = fields.Selection([
            (None, ''),
            ('saline', 'saline'),
            ('silicone_intact', 'silicone intact'),
            ('silicone_ruptured', 'silicone ruptured'),
            ('other', 'other implant material'),
            ], 'Implant material', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_lumen_type = fields.Selection([
            (None, ''),
            ('single', 'single'),
            ('double', 'double'),
            ('other', 'other'),
            ], 'Lumen type', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_implant_location = fields.Selection([
            (None, ''),
            ('retroglandular', 'retroglandular'),
            ('retropectoral', 'retropectoral'),
            ], 'Implant location', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_abnormal_implant_contour = fields.Selection([
            (None, ''),
            ('focal_bulge', 'focal bulge'),
            ], 'Abnormal implant contour', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_intracapsular = fields.Selection([
            (None, ''),
            ('radial', 'radial folds'),
            ('subcapsular', 'subcapsular line'),
            ('keyhole', 'keyhole sign (teardrop, noose)'),
            ('linguine', 'linguine sign'),
            ], 'Intracapsular silicone findings', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_extracapsular = fields.Selection([
            (None, ''),
            ('breast', 'breast'),
            ('lymph_nodes', 'lymph nodes'),
            ], 'Extracapsular silicone', sort=False,
        states=_mri_states, depends=['method'])
    mri_implants_water_droplets = fields.Boolean(
        'Water droplets',
        states=_mri_states, depends=['method'])
    mri_implants_peri_implant_fluid = fields.Boolean(
        'Peri-implant fluid',
        states=_mri_states, depends=['method'])

    del _ultrasound_states, _mammo_states, _mri_states

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order = [
            ('finding_date', 'DESC'),
            ('id', 'DESC'),
            ]

    @staticmethod
    def default_method():
        return 'ultrasound'

    @staticmethod
    def default_evaluated_by():
        return get_health_professional(required=False)

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//group[@id="finding_ultrasound"]', "states", {
                    'invisible': (Eval('method') != 'ultrasound'),
                    }),
            ('//group[@id="finding_mammography"]', "states", {
                    'invisible': (Eval('method') != 'mammography'),
                    }),
            ('//group[@id="finding_mri"]', "states", {
                    'invisible': (Eval('method') != 'mri'),
                    })]

    @fields.depends('bi_rads')
    def on_change_with_bi_rads_comment(self, name=None):
        if self.bi_rads:
            return self.bi_rads.comment


class BIRADS(ModelSQL, ModelView):
    'BI-RADS Classification'
    __name__ = 'gnuhealth.imaging.birads'

    code = fields.Char('Code')
    classification = fields.Char('Classification')
    probability_of_malignancy = fields.Char('Probability of Malignancy',
        help='Probability in percent')
    comment = fields.Text('Comment')

    def get_rec_name(self, name):
        return '%s: %s' % (self.code, self.classification)
