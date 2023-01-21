# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval


class MammographyPatient(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient'

    doctor_referrals = fields.One2Many('ir.attachment',
        'resource', "Doctor's Referrals")
    # Post-Treatment Surveillance: add here but possibly better located or
    # calculated from patient data/evaluations
    #  Main condition (e.g. D05.9 : Carcinoma in situ of breast, unspecified) and/or
    #  Treatment Plan and/or
    #  Procedures (e.g. 3-193 : RADIOGRAPHY OF MAMMARY GLAND)
    post_treatment_surveillance = fields.Boolean(
        "Is the patient currently undergoing post-treatment surveillance?")
    post_treatment_surveillance_comment = fields.Text(
        "Post Treatment Surveillance",
        states={
            'invisible': ~Eval('post_treatment_surveillance'),
            }, depends=['post_treatment_surveillance'])
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

    @staticmethod
    def default_post_treatment_surveillance():
        return False


class PatientEvaluation(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient.evaluation'

    @classmethod
    def __setup__(cls):
        super().__setup__()
        for item in (('screening', 'Screening'), ('diagnostic', 'Diagnostic')):
            if item not in cls.visit_type.selection:
                cls.visit_type.selection.append(item)

    # Clinical complaints -> present_illness/notes_complaint
    # https://savannah.gnu.org/bugs/index.php?63535
    breast_cancer_history_person = fields.Text(
        "Personal Breast Cancer History")
    breast_cancer_history_family = fields.Text(
        "Family Breast Cancer History")
