# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.i18n import gettext
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        states_required = {
            'required': Bool(Eval('is_person'))
            }
        cls.name.states.update(states_required)
        cls.lastname.states.update(states_required)
        cls.dob.states.update(states_required)

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//page[@id="party_gnuhealth_extended"]', "states", {
                    'invisible': True,
                    })]

    @staticmethod
    def default_gender():
        return 'f'


class MammographyPatient(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient'

    doctor_referrals = fields.One2Many('ir.attachment',
        'resource', "Doctor's Referrals")
    evaluations = fields.One2Many('gnuhealth.patient.evaluation', 'patient',
        "Evaluations",
        domain=[
            ('patient', '=', Eval('id')),
            ], depends=['id'])
    imaging_test_results = fields.One2Many('gnuhealth.imaging.test.result',
        'patient', "Mammography Reports",
        domain=[
            ('patient', '=', Eval('id')),
            ], depends=['id'])
    findings = fields.One2Many('gnuhealth.imaging.finding', 'patient',
        'Findings',
        domain=[
            ('patient', '=', Eval('id')),
            ], depends=['id'])
    biopsies = fields.Text('Biopsies')

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # Enable the editing of parties from the patient relate
        cls.name.states['readonly'] = False


screening_types = [
    (None, ''),
    ('screening_first_time',
        'Screening: First-time Routine Screening Visit'),
    ('screening_return', 'Screening: Routine Annual Screening'),
    ('screening_second_opinion', 'Screening: Get Second Opinion'),
    ]
diagnostic_types = [
    (None, ''),
    ('diagnostic_recall', 'Diagnostic: Recall'),
    ('diagnostic_short_term',
        'Diagnostic: Short-term follow-up '
        '(~6 months since last screening visit)'),
    ('diagnostic_symptoms', 'Diagnostic: Breast symptoms'),
    ('diagnostic_post_treat', 'Diagnostic: Post-treatment surveillance'),
    ]
vara_types = screening_types + diagnostic_types


class PatientEvaluation(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient.evaluation'

    # Clinical complaints -> present_illness/notes_complaint
    # https://savannah.gnu.org/bugs/index.php?63535
    post_treatment_surveillance = fields.Text(
        "Post Treatment Surveillance Comment",
        states={
            'invisible': ~(Eval('visit_type') == 'diagnostic_post_treat'),
            }, depends=['visit_type'])
    breast_lump = fields.Selection('get_location_selection',
        'New lump in breast or axilla (i.e. armpit)',
        sort=False)
    breast_lump_string = breast_lump.translated('breast_lump')
    breast_swelling = fields.Selection('get_location_selection',
        'Thickening or swelling of part of the breast',
        sort=False)
    breast_swelling_string = breast_swelling.translated('breast_swelling')
    breast_skin_irritation = fields.Selection('get_location_selection',
        'Irritation or dimpling of breast skin',
        sort=False)
    breast_skin_irritation_string = breast_skin_irritation.translated(
        'breast_skin_irritation')
    breast_nipple_changes = fields.Selection('get_location_selection',
        'Nipple changes (e.g. redness, flaky skin, inversion, discharge)',
        sort=False)
    breast_nipple_changes_string = breast_nipple_changes.translated(
        'breast_nipple_changes')
    breast_operational_intervention = fields.Boolean(
        "Was there any operational intervention in the breast?")
    breast_operational_intervention_type = fields.Selection([
            (None, ''),
            ('mastectomy', 'Mastectomy'),
            ('conservative', 'Conservative Breast Surgery'),
            ('benign_lumpectomy', 'Benign Lumpectomy'),
            ('augmentation', 'Breast Augmentation Surgery'),
            ('reduction', 'Breast Reduction Surgery'),
            ('other', 'Other'),
            ], 'Type of Breast Surgery',
        states={
            'invisible': ~Eval('breast_operational_intervention'),
            'required': Bool(Eval('breast_operational_intervention')),
            }, depends=['breast_operational_intervention'])
    breast_operational_intervention_comment = fields.Char('Other Surgery Type',
        states={
            'invisible': (
                (Eval('breast_operational_intervention_type') != 'other')
                | ~Eval('breast_operational_intervention')),
            'required': (
                (Eval('breast_operational_intervention_type') == 'other')),
            }, depends=['breast_operational_intervention',
            'breast_operational_intervention_type'])
    woman_pregnant = fields.Boolean("Is the woman pregnant?")
    woman_lactating = fields.Boolean(
        "Is the woman lactating / breast feeding?")
    breast_cancer_history_person = fields.Boolean(
        "Personal Breast Cancer History")
    breast_cancer_history_person_text = fields.Text(
        "Personal Breast Cancer History Text",
        states={
            'invisible': ~Eval('breast_cancer_history_person'),
            }, depends=['breast_cancer_history_person'])
    sequence_number = fields.Char("Sequence Number",
        states={
            'invisible': ~Eval('breast_cancer_history_person'),
            }, depends=['breast_cancer_history_person'])
    diagnosis_date = fields.Date('Date of diagnosis',
        states={
            'invisible': ~Eval('breast_cancer_history_person'),
            }, depends=['breast_cancer_history_person'])
    surgery_date = fields.Date('Date of surgery',
        states={
            'invisible': ~Eval('breast_cancer_history_person'),
            }, depends=['breast_cancer_history_person'])

    breast_cancer_history_family = fields.Boolean(
        "Family Breast Cancer History")
    breast_cancer_history_family_text = fields.Text(
        "Family Breast Cancer History Text",
        states={
            'invisible': ~Eval('breast_cancer_history_family'),
            }, depends=['breast_cancer_history_family'])
    known_brca_mutation = fields.Boolean(
        "Known BRCA1/2 mutation carrier?",
        states={
            'invisible': ~Eval('breast_cancer_history_family'),
            }, depends=['breast_cancer_history_family'])
    genetic_risks = fields.Function(
        fields.One2Many('gnuhealth.patient.genetic.risk',
        None, "Genetic Information",
            domain=[('patient', '=', Eval('patient'))],
            states={
                'invisible': ~Eval('known_brca_mutation'),
                }, depends=['known_brca_mutation', 'patient']),
        'get_genetic_risks', setter='set_genetic_risks')

    def get_genetic_risks(self, name):
        return [r.id for r in self.patient.genetic_risks]

    @classmethod
    def set_genetic_risks(cls, evaluations, name, values):
        Risk = Pool().get('gnuhealth.patient.genetic.risk')
        for value in values:
            action = value[0]
            if action == 'create':
                Risk.create(value[1])
            elif action == 'write':
                value.pop(0)
                items = {value[i][0]: value[i + 1]
                    for i in range(0, len(value), 2)}
                for item in items:
                    risk = Risk.browse([item])
                    Risk.write(risk, items[item])
            elif action == 'delete':
                risks = Risk.browse(value[1])
                Risk.delete(risks)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        #for item in vara_types:
        #    if item not in cls.visit_type.selection:
        #        cls.visit_type.selection.append(item)
        cls.visit_type.selection = vara_types
        cls.visit_type.states['required'] = True

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//separator[@id="separator_post_treat"]', "states", {
                    'invisible': ~(
                        Eval('visit_type') == 'diagnostic_post_treat'),
                    })]

    @staticmethod
    def default_breast_cancer_history_person():
        return False

    @staticmethod
    def default_breast_cancer_history_family():
        return False

    @staticmethod
    def default_known_brca_mutation():
        return False

    @classmethod
    def get_location_selection(cls):
        return [
            (None, ''),
            ('left_breast', 'Left Breast'),
            ('right_breast', 'Right Breast'),
            ('both', 'Both Breasts'),
            ]
