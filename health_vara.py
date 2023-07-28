# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.
from trytond.i18n import gettext
from trytond.model import fields, DeactivableMixin
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Bool, Eval
import re


def normalise_mobile_number(value):
    # treat whitespace-only values the same as None
    value = None if (value is None) or (value == '') or (value.isspace()) else value

    # replace leading '00' with '+' to standardise international numbers
    value = re.sub('^00', '+', value) if value else None

    return value


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

        mobile_field = getattr(cls, 'mobile')
        setattr(mobile_field, 'setter', 'set_mobile')
        setattr(mobile_field, 'searcher', 'search_mobile')
        setattr(mobile_field, 'readonly', False)

    @classmethod
    def view_attributes(cls):
        return super().view_attributes() + [
            ('//page[@id="party_gnuhealth_extended"]', "states", {
                    'invisible': True,
                    })]

    @staticmethod
    def default_gender():
        return 'f'

    @staticmethod
    def default_name_representation():
        # Possible values are listed here:
        # https://hg.savannah.gnu.org/hgweb/health/file/0540c046667a/tryton/health/health.py#l338
        #  None  => ''
        # 'pgfs' => 'Prefix Given Family, Suffix'
        # 'gf'   => 'Given Family'
        # 'fg'   => 'Family, Given'
        # 'cjk'  => 'CJK: Family+Given'
        return 'gf'

    @classmethod
    def search_mobile(cls, _name, clause):
        res = []
        op = clause[1]
        value = clause[2]

        res.append(('contact_mechanisms.type', '=', 'mobile'))
        res.append(('contact_mechanisms.value', op, value))
        return res

    @classmethod
    def set_mobile(cls, parties, _field_name, value):
        Party = Pool().get('party.party')
        value = normalise_mobile_number(value)

        for party in parties:
            mobile = next((mechanisms for
                           mechanisms in party.contact_mechanisms
                           if mechanisms.type == 'mobile' and mechanisms.active),
                          None)

            if value is None and mobile is None:
                # we have nothing and want nothing, so do nothing!
                change = None
            elif value is None:
                # we had a value, but want nothing, so delete it.
                change = {'contact_mechanisms': [['delete', [mobile.id]]]}
            elif mobile is None:
                # we have no value, but want one, so create it.
                change = {'contact_mechanisms': [['create', [{'type': 'mobile', 'value': value}]]]}
            else:
                # update the existing value with a new one.
                change = {'contact_mechanisms': [['write', [mobile.id], {'value': value}]]}

            if change:
                Party.write([party], change)


def get_party_val(patient_field_name, passthrough_config_key, default_val):
    return MammographyPatient.patient_passthrough_fields \
        .get(patient_field_name, {}) \
        .get(passthrough_config_key, default_val)


def get_party_field_name(patient_field_name):
    return get_party_val(patient_field_name, 'party_field', patient_field_name)


class MammographyPatient(metaclass=PoolMeta):
    __name__ = 'gnuhealth.patient'

    # map of patient field names to config for where (party_field) to set the value on the party
    patient_passthrough_fields = {
        'firstname': {'party_field': 'name'},
        'lastname': {},
        'dob': {},
        'gender': {},
        'mobile': {'required': False}
    }

    partner_patient_id = fields.Char('Patient ID', select=True)

    doctor_referrals = fields.One2Many('ir.attachment',
        'resource', "Doctor's Referrals")
    evaluations = fields.One2Many('gnuhealth.patient.evaluation', 'patient',
        "Evaluations",
        domain=[
            ('patient', '=', Eval('id')),
            ], depends=['id'])
    imaging_test_requests = fields.One2Many('gnuhealth.imaging.test.request',
        'patient', "Imaging Requests",
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
    opinion = fields.Text('Opinion')
    recommendation = fields.Text('Recommendation')

    firstname = fields.Function(
        fields.Char('Name'), 'get_firstname',
        searcher='search_firstname')

    mobile = fields.Function(
        fields.Char('Mobile', help='Mobile numbers should start with a country code +XX'), 'get_mobile',
        searcher='search_mobile')

    most_recent_imaging_request_datetime = fields.Function(
        fields.DateTime('Last Imaging Request', depends=['imaging_test_requests']),
        'get_most_recent_imaging_request_datetime'
    )

    @classmethod
    def __setup__(cls):
        super().__setup__()
        # Enable the editing of parties from the patient relate
        cls.name.states['readonly'] = False
        cls.name.states['required'] = False

        # ensures all the patient fields that should pass on values to party
        # are settable and inherit the 'required' state
        for patient_field_name in MammographyPatient.patient_passthrough_fields:
            patient_field = getattr(cls, patient_field_name)
            setattr(patient_field, 'setter', 'set_passthrough_field')
            setattr(patient_field, 'readonly', False)
            setattr(patient_field, 'required', get_party_val(patient_field_name, 'required', True))

    @classmethod
    def create(cls, vlist):
        # overrides creation to also create a new party
        # with sensible defaults derived from the patient fields
        vlist = [x.copy() for x in vlist]
        Party = Pool().get('party.party')

        for values in vlist:
            # sets the default party data
            party_data = {'fed_country': '',
                          'active': True,
                          'is_patient': True,
                          'is_person': True}

            # passthrough the appropriate values into party_data
            for patient_field_name in MammographyPatient.patient_passthrough_fields:
                party_field_name = get_party_field_name(patient_field_name)
                party_data[party_field_name] = values.get(patient_field_name)

            # creates a party, and reference it from the patient by its id
            party, = Party.create([party_data])
            values['name'] = party.id
        return super(MammographyPatient, cls).create(vlist)

    def get_firstname(self, _name):
        # the party is stored in a field called name,
        # hence 'name.name' really means 'party.name'
        return self.name.name

    @classmethod
    def search_firstname(cls, _name, clause):
        res = []
        op = clause[1]
        value = clause[2]
        # the party is stored in a field called name,
        # hence 'name.name' really means 'party.name'
        res.append(('name.name', op, value))
        return res

    def get_mobile(self, _name):
        # the party is stored in a field called name,
        # hence 'name.name' really means 'party.name'
        return self.name.mobile

    @classmethod
    def search_mobile(cls, _name, clause):
        res = []
        op = clause[1]
        value = clause[2]
        # the party is stored in a field called name,
        # hence 'name.name' really means 'party.name'
        res.append(('name.mobile', op, value))
        return res

    def get_most_recent_imaging_request_datetime(self, _name):
        if self.imaging_test_requests:
            dt = max(i.date for i in self.imaging_test_requests)
            return dt

    @classmethod
    def set_passthrough_field(cls, patients, patient_field_name, value):
        # Passes the value to Party, to be written there instead
        Party = Pool().get('party.party')
        party_field_name = get_party_field_name(patient_field_name)
        Party.write([patient.name for patient in patients], {party_field_name: value})

    # Overrides to add in the general search by 'partner_patient_id', otherwise identical
    @classmethod
    def search_rec_name(cls, _name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
                ('puid',) + tuple(clause[1:]),
                ('name',) + tuple(clause[1:]),
                ('lastname',) + tuple(clause[1:]),
                ('partner_patient_id',) + tuple(clause[1:]),
                ]


screening_types = [
    ('screening_first_time',
        'Screening: First-time Routine Screening Visit'),
    ('screening_return', 'Screening: Routine Annual Screening'),
    ('screening_second_opinion', 'Screening: Get Second Opinion'),
    ]
diagnostic_types = [
    ('diagnostic_recall', 'Diagnostic: Recall'),
    ('diagnostic_short_term',
        'Diagnostic: Short-term follow-up '
        '(~6 months since last screening visit)'),
    ('diagnostic_symptoms', 'Diagnostic: Breast symptoms'),
    ('diagnostic_post_treat', 'Diagnostic: Post-treatment surveillance'),
    ]
vara_types = [(None, '')] + screening_types + diagnostic_types


class PatientEvaluation(DeactivableMixin, metaclass=PoolMeta):
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
        "Does the woman have a personal history of breast cancer?")
    breast_cancer_history_person_text = fields.Text(
        "Personal Breast Cancer History Text",
        states={
            'invisible': ~Eval('breast_cancer_history_person'),
            }, depends=['breast_cancer_history_person'])
    cancer_history_person = fields.Boolean(
        "Did the woman have any other cancer in the past?")
    cancer_history_person_text = fields.Text(
        "Personal Cancer History Text",
        states={
            'invisible': ~Eval('cancer_history_person'),
            }, depends=['cancer_history_person'])
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
        "Does the woman's family have a history of breast cancer?")
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
        # for item in vara_types:
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
        # Requires using gettext and /data/messages/messages.xml objects as apparently it
        # won't be supported for translations:
        # https://foss.heptapod.net/tryton/tryton/-/issues/6277
        return [
            (None, ''),
            ('left_breast', gettext('health_vara.evaluation_location_selection_left_breast')),
            ('right_breast', gettext('health_vara.evaluation_location_selection_right_breast')),
            ('both', gettext('health_vara.evaluation_location_selection_both_breasts')),
            ]

    # Remove when Upstream Bug is solved (#4932)
    # https://savannah.gnu.org/bugs/index.php?63959
    @fields.depends('patient')
    def on_change_patient(self):
        if self.patient.id > 0:
            super().on_change_patient()
