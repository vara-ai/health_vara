# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # Gender shouldn't be required
        cls.gender.states['required'] = False

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//page[@id="party_gnuhealth_extended"]', "states", {
                    'invisible': True,
                    })]


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

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # Enable the editing of parties from the patient relate
        cls.name.states['readonly'] = False


screening_types = [
    (None, ''),
    ('screening_first_time',
        'Screening: First-time Routine Screening Visit'),
    ('screening_return', 'Screening: Return / Follow-up Visit'),
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
        "Post Treatment Surveillance",
        states={
            'invisible': ~(Eval('visit_type') == 'diagnostic_post_treat'),
            }, depends=['visit_type'])

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
    genetic_risks = fields.One2Many('gnuhealth.patient.genetic.risk',
        'patient', "Genetic Information",
        states={
            'invisible': ~Eval('known_brca_mutation'),
            }, depends=['known_brca_mutation'])

    @classmethod
    def __setup__(cls):
        super().__setup__()
        for item in vara_types:
            if item not in cls.visit_type.selection:
                cls.visit_type.selection.append(item)

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
