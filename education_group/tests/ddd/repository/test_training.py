##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from base.models.certificate_aim import CertificateAim
from base.models.education_group import EducationGroup
from base.models.education_group_certificate_aim import EducationGroupCertificateAim
from base.models.education_group_year import EducationGroupYear as EducationGroupYearModelDb
from base.models.education_group_year_domain import EducationGroupYearDomain
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.campus import CampusFactory as CampusModelDbFactory
from base.tests.factories.certificate_aim import CertificateAimFactory as CertificateAimModelDbFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import EntityVersionFactory as EntityVersionModelDbFactory
from education_group.ddd.domain import exception
from education_group.ddd.domain.training import Training, TrainingIdentity
from education_group.ddd.repository.training import TrainingRepository
from education_group.tests.ddd.factories.campus import CampusIdentityFactory
from education_group.tests.ddd.factories.diploma import DiplomaAimFactory, DiplomaAimIdentityFactory
from education_group.tests.ddd.factories.isced_domain import IscedDomainIdentityFactory
from education_group.tests.ddd.factories.study_domain import StudyDomainIdentityFactory, StudyDomainFactory
from education_group.tests.ddd.factories.training import TrainingFactory, TrainingIdentityFactory
from reference.models.domain import Domain
from reference.tests.factories.domain import DomainFactory as DomainModelDbFactory
from reference.tests.factories.domain_isced import DomainIscedFactory as DomainIscedFactoryModelDb
from reference.tests.factories.language import LanguageFactory as LanguageModelDbFactory


class TestTrainingRepositoryCreateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.year = AcademicYearFactory(current=True).year

        cls.repository = TrainingRepository()

        cls.education_group_type = TrainingEducationGroupTypeFactory()
        cls.language = LanguageModelDbFactory()
        cls.study_domain = DomainModelDbFactory()
        cls.secondary_study_domain = DomainModelDbFactory()
        cls.isced_domain = DomainIscedFactoryModelDb()
        cls.entity_version = EntityVersionModelDbFactory()
        cls.campus = CampusModelDbFactory()
        cls.certificate_aim = CertificateAimModelDbFactory()

        study_domain_identity = StudyDomainIdentityFactory(
            decree_name=cls.study_domain.decree.name,
            code=cls.study_domain.code
        )
        diploma_aim_identity = DiplomaAimIdentityFactory(
            code=cls.certificate_aim.code,
            section=cls.certificate_aim.section
        )
        campus_identity = CampusIdentityFactory(name=cls.campus.name, university_name=cls.campus.organization.name)
        training_identity = TrainingIdentityFactory(year=cls.year)
        cls.training = TrainingFactory(
            entity_id=training_identity,
            entity_identity=training_identity,
            start_year=cls.year,
            end_year=cls.year,
            type=TrainingType[cls.education_group_type.name],
            main_language__name=cls.language.name,
            main_domain__entity_id=study_domain_identity,
            isced_domain__entity_id=IscedDomainIdentityFactory(code=cls.isced_domain.code),
            management_entity__acronym=cls.entity_version.acronym,
            administration_entity__acronym=cls.entity_version.acronym,
            teaching_campus=campus_identity,
            enrollment_campus=campus_identity,
            secondary_domains=[
                StudyDomainFactory(entity_id=study_domain_identity)
            ],
            diploma__aims=[
                DiplomaAimFactory(entity_id=diploma_aim_identity)
            ]
        )

    def test_fields_mapping(self):
        entity_id = self.repository.create(self.training)

        education_group_year = EducationGroupYearModelDb.objects.get(
            acronym=entity_id.acronym,
            academic_year__year=entity_id.year,
        )
        assert_training_model_equals_training_domain(
            self,
            education_group_year,
            self.training,
            self.entity_version.entity_id
        )
        
        # Secondary domains
        qs = EducationGroupYearDomain.objects.filter(education_group_year=education_group_year)
        self.assertEqual(1, qs.count())
        educ_group_year_domain = qs.get()
        self.assertEqual(
            educ_group_year_domain.domain,
            Domain.objects.get(
                code=self.training.secondary_domains[0].entity_id.code,
                decree__name=self.training.secondary_domains[0].entity_id.decree_name
            )
        )

        # Certificate aims
        qs_aims = EducationGroupCertificateAim.objects.filter(education_group_year=education_group_year)
        self.assertEqual(1, qs_aims.count())
        educ_group_certificate_aim = qs_aims.get()
        self.assertEqual(
            educ_group_certificate_aim.certificate_aim,
            CertificateAim.objects.get(code=self.training.diploma.aims[0].entity_id.code)
        )


class TestTrainingRepositoryUpdateMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.entity_version = EntityVersionModelDbFactory()
        cls.education_group_year = EducationGroupYearFactory(
            management_entity=cls.entity_version.entity,
            administration_entity=cls.entity_version.entity,
            academic_year__current=True

        )

        cls.training = TrainingRepository.get(
            TrainingIdentityFactory(
                acronym=cls.education_group_year.acronym,
                year=cls.education_group_year.academic_year.year
            )
        )
        cls.domain = DomainModelDbFactory()
        cls.isced_domain = DomainIscedFactoryModelDb()
        cls.campus = CampusModelDbFactory()
        cls.study_domain = DomainModelDbFactory()
        cls.certificate_aim = CertificateAimModelDbFactory()
        AcademicYearFactory(year=2025)

    def test_should_save_updated_values(self):
        study_domain_identity = StudyDomainIdentityFactory(
            decree_name=self.study_domain.decree.name,
            code=self.study_domain.code
        )
        diploma_aim_identity = DiplomaAimIdentityFactory(
            code=self.certificate_aim.code,
            section=self.certificate_aim.section
        )
        updated_training = TrainingFactory(
            entity_identity=self.training.entity_identity,
            code=self.training.code,
            start_year=self.training.start_year,
            end_year=2025,
            identity_through_years=self.training.identity_through_years,
            type=self.training.type,
            main_language=self.training.main_language,
            main_domain=StudyDomainFactory(
                entity_id__decree_name=self.domain.decree.name,
                entity_id__code=self.domain.code
            ),
            isced_domain__entity_id__code=self.isced_domain.code,
            management_entity=self.training.management_entity,
            administration_entity=self.training.administration_entity,
            teaching_campus=CampusIdentityFactory(
                name=self.campus.name,
                university_name=self.campus.organization.name
            ),
            enrollment_campus=CampusIdentityFactory(
                name=self.campus.name,
                university_name=self.campus.organization.name
            ),
            secondary_domains=[
                StudyDomainFactory(entity_id=study_domain_identity)
            ],
            diploma__aims=[
                DiplomaAimFactory(entity_id=diploma_aim_identity)
            ]
        )

        TrainingRepository.update(updated_training)

        self.education_group_year.refresh_from_db()
        assert_training_model_equals_training_domain(
            self,
            self.education_group_year,
            updated_training,
            self.entity_version.entity.id
        )


class TestTrainingRepositoryGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_year = EducationGroupYearFactory(acronym="LOSIS4587")

    def test_should_raise_exception_when_no_matching_training(self):
        training_identity_with_no_match = TrainingIdentityFactory(acronym="NO MATCH")
        with self.assertRaises(exception.TrainingNotFoundException):
            TrainingRepository.get(training_identity_with_no_match)

    def test_should_return_a_training_when_matching_training_exists(self):
        training_identity = generate_training_identity_from_education_group_year(self.education_group_year)

        result = TrainingRepository.get(training_identity)
        self.assertIsInstance(result, Training)


class TestTrainingRepositorySearchMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_years = [
            EducationGroupYearFactory(acronym="LOSIS5897", academic_year__year=2015),
            EducationGroupYearFactory(acronym="MEDE8523", academic_year__year=2018)
        ]

    def test_should_return_empty_list_when_no_matching_trainings(self):
        training_identity_with_no_match = TrainingIdentityFactory(acronym="NO MATCH")

        result = TrainingRepository.search([training_identity_with_no_match])
        self.assertListEqual([], result)

    def test_should_return_list_of_trainings_when_matching_trainings(self):
        training_identities = [
            generate_training_identity_from_education_group_year(egy)
            for egy in self.education_group_years
        ]

        result = TrainingRepository.search(training_identities)
        self.assertEqual(len(training_identities), len(result))


class TestTrainingDeleteMethod(TestCase):
    def test_should_raise_exception_when_no_matching_training_to_delete(self):
        training_identity_with_no_match = TrainingIdentityFactory(acronym="NO MATCH")

        with self.assertRaises(exception.TrainingNotFoundException):
            TrainingRepository.delete(training_identity_with_no_match)

    def test_should_delete_education_group_year_when_matching_training_to_delete(self):
        education_group_year_db = EducationGroupYearFactory(acronym="LOSIS5897", academic_year__year=2017)
        EducationGroupYearFactory(
            acronym="LOSIS5897",
            academic_year__year=2016,
            education_group=education_group_year_db.education_group
        )
        training_identity = generate_training_identity_from_education_group_year(education_group_year_db)

        TrainingRepository.delete(training_identity)

        with self.assertRaises(EducationGroupYearModelDb.DoesNotExist):
            EducationGroupYearModelDb.objects.get(pk=education_group_year_db.pk)

    def test_should_delete_education_group_when_last_training_deleted(self):
        education_group_year_db = EducationGroupYearFactory(acronym="LOSIS5897", academic_year__year=2017)

        training_identity = generate_training_identity_from_education_group_year(education_group_year_db)

        TrainingRepository.delete(training_identity)

        with self.assertRaises(EducationGroup.DoesNotExist):
            EducationGroup.objects.get(pk=education_group_year_db.education_group.pk)


def generate_training_identity_from_education_group_year(
        education_group_year_obj: 'EducationGroupYearModelDb') -> 'TrainingIdentity':
    return TrainingIdentityFactory(
        acronym=education_group_year_obj.acronym,
        year=education_group_year_obj.academic_year.year
    )


def assert_training_model_equals_training_domain(
        test_instance: 'TestCase',
        education_group_year: EducationGroupYearModelDb,
        training_domain_obj: Training,
        entity_version_id: int):
    # TODO assert entities
    test_instance.assertEqual(education_group_year.education_group.start_year.year, training_domain_obj.start_year)
    test_instance.assertEqual(
        education_group_year.education_group.end_year.year
        if education_group_year.education_group.end_year else None,
        training_domain_obj.end_year
    )

    test_instance.assertEqual(education_group_year.acronym, training_domain_obj.entity_id.acronym)
    test_instance.assertEqual(education_group_year.academic_year.year, training_domain_obj.entity_id.year)
    test_instance.assertEqual(education_group_year.education_group_type.name, training_domain_obj.type.name)
    test_instance.assertEqual(education_group_year.management_entity_id, entity_version_id)
    test_instance.assertEqual(education_group_year.administration_entity_id, entity_version_id)
    test_instance.assertEqual(education_group_year.credits, int(training_domain_obj.credits))
    test_instance.assertEqual(education_group_year.schedule_type, training_domain_obj.schedule_type.name)
    test_instance.assertEqual(education_group_year.duration, training_domain_obj.duration)
    test_instance.assertEqual(education_group_year.title, training_domain_obj.titles.title_fr)
    test_instance.assertEqual(education_group_year.title_english, training_domain_obj.titles.title_en)
    test_instance.assertEqual(education_group_year.partial_title, training_domain_obj.titles.partial_title_fr)
    test_instance.assertEqual(education_group_year.partial_title_english, training_domain_obj.titles.partial_title_en)
    test_instance.assertEqual(education_group_year.keywords, training_domain_obj.keywords)
    test_instance.assertEqual(education_group_year.internship, training_domain_obj.internship_presence.name)
    test_instance.assertEqual(education_group_year.enrollment_enabled, training_domain_obj.is_enrollment_enabled)
    test_instance.assertEqual(education_group_year.web_re_registration, training_domain_obj.has_online_re_registration)
    test_instance.assertEqual(education_group_year.partial_deliberation, training_domain_obj.has_partial_deliberation)
    test_instance.assertEqual(education_group_year.admission_exam, training_domain_obj.has_admission_exam)
    test_instance.assertEqual(education_group_year.dissertation, training_domain_obj.has_dissertation)
    test_instance.assertEqual(
        education_group_year.university_certificate,
        training_domain_obj.produce_university_certificate
    )
    test_instance.assertEqual(education_group_year.decree_category, training_domain_obj.decree_category.name)
    test_instance.assertEqual(education_group_year.rate_code, training_domain_obj.rate_code.name)
    test_instance.assertEqual(education_group_year.primary_language.name, training_domain_obj.main_language.name)
    test_instance.assertEqual(education_group_year.english_activities, training_domain_obj.english_activities.name)
    test_instance.assertEqual(
        education_group_year.other_language_activities,
        training_domain_obj.other_language_activities.name
    )
    test_instance.assertEqual(education_group_year.internal_comment, training_domain_obj.internal_comment)
    test_instance.assertEqual(education_group_year.main_domain.code, training_domain_obj.main_domain.entity_id.code)
    test_instance.assertEqual(education_group_year.isced_domain.code, training_domain_obj.isced_domain.entity_id.code)
    test_instance.assertEqual(education_group_year.main_teaching_campus.name, training_domain_obj.teaching_campus.name)
    test_instance.assertEqual(education_group_year.enrollment_campus.name, training_domain_obj.enrollment_campus.name)
    test_instance.assertEqual(
        education_group_year.other_campus_activities,
        training_domain_obj.other_campus_activities.name
    )
    test_instance.assertEqual(education_group_year.funding, training_domain_obj.funding.can_be_funded)
    test_instance.assertEqual(
        education_group_year.funding_direction,
        training_domain_obj.funding.funding_orientation.name
    )
    test_instance.assertEqual(education_group_year.funding_cud, training_domain_obj.funding.can_be_international_funded)
    test_instance.assertEqual(
        education_group_year.funding_direction_cud,
        training_domain_obj.funding.international_funding_orientation.name
    )
    test_instance.assertEqual(education_group_year.hops.ares_study, training_domain_obj.hops.ares_code)
    test_instance.assertEqual(education_group_year.hops.ares_graca, training_domain_obj.hops.ares_graca)
    test_instance.assertEqual(education_group_year.hops.ares_ability, training_domain_obj.hops.ares_authorization)
    test_instance.assertEqual(education_group_year.co_graduation, training_domain_obj.co_graduation.code_inter_cfb)
    test_instance.assertEqual(
        education_group_year.co_graduation_coefficient,
        training_domain_obj.co_graduation.coefficient
    )
    test_instance.assertEqual(education_group_year.academic_type, training_domain_obj.academic_type.name)
    test_instance.assertEqual(education_group_year.duration_unit, training_domain_obj.duration_unit.name)
    test_instance.assertEqual(education_group_year.professional_title, training_domain_obj.diploma.professional_title)
    test_instance.assertEqual(education_group_year.joint_diploma, training_domain_obj.diploma.leads_to_diploma)
    test_instance.assertEqual(education_group_year.diploma_printing_title, training_domain_obj.diploma.printing_title)
    test_instance.assertEqual(education_group_year.active, training_domain_obj.status.name)
