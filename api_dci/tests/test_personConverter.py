"""
Unit tests for PersonConverter

Tests the conversion between DCI Person format and OpenIMIS Individual model.
"""
from django.test import TestCase
from datetime import date
from api_dci.converters.person_converter import PersonConverter


class PersonConverterTestCase(TestCase):
    """
    Test cases for PersonConverter class.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.test_dci_person = {
            "@type": "Person",
            "identifier": [
                {
                    "type": "test_id",
                    "value": "test:person:123",
                    "system": "test"
                }
            ],
            "name": {
                "given_name": "John",
                "family_name": "Doe",
                "full_name": "John Doe"
            },
            "birth_date": "1990-01-15T00:00:00Z",
            "sex": "male",
            "phone_number": ["+1234567890"],
            "email": ["john.doe@example.com"]
        }

    def test_individual_to_dci_person_basic_fields(self):
        """
        Test conversion of Individual to DCI Person with basic fields.
        """
        # TODO: Implement test
        # This test should:
        # 1. Create a mock Individual instance
        # 2. Convert to DCI Person
        # 3. Verify all basic fields are correctly mapped
        pass

    def test_individual_to_dci_person_gender_mapping(self):
        """
        Test gender mapping from Individual to DCI Person.
        """
        # TODO: Implement test
        # This test should verify:
        # - M -> Male
        # - F -> Female
        # - O -> Other
        pass

    def test_individual_to_dci_person_missing_fields(self):
        """
        Test conversion when Individual has missing optional fields.
        """
        # TODO: Implement test
        # This test should verify graceful handling of None values
        pass

    def test_dci_person_to_individual_data_basic_fields(self):
        """
        Test conversion of DCI Person to Individual data with basic fields.
        """
        result = PersonConverter.dci_person_to_individual_data(self.test_dci_person)

        # Verify basic field mappings
        self.assertEqual(result['first_name'], "John")
        self.assertEqual(result['last_name'], "Doe")
        self.assertEqual(result['dob'], date(1990, 1, 15))
        self.assertEqual(result['gender_code'], 'M')
        self.assertEqual(result['phone'], "+1234567890")
        self.assertEqual(result['email'], "john.doe@example.com")

        # Verify json_ext contains sex
        self.assertIn('json_ext', result)
        self.assertEqual(result['json_ext']['sex'], 'male')

    def test_dci_person_to_individual_data_gender_reverse_mapping(self):
        """
        Test reverse gender mapping from DCI Person to Individual.
        """
        # Test male -> M
        person = {"sex": "male"}
        result = PersonConverter.dci_person_to_individual_data(person)
        self.assertEqual(result['gender_code'], 'M')

        # Test female -> F
        person = {"sex": "female"}
        result = PersonConverter.dci_person_to_individual_data(person)
        self.assertEqual(result['gender_code'], 'F')

        # Test others -> O
        person = {"sex": "others"}
        result = PersonConverter.dci_person_to_individual_data(person)
        self.assertEqual(result['gender_code'], 'O')

        # Test unknown -> U
        person = {"sex": "unknown"}
        result = PersonConverter.dci_person_to_individual_data(person)
        self.assertEqual(result['gender_code'], 'U')

    def test_dci_person_to_individual_data_missing_fields(self):
        """
        Test conversion when DCI Person has missing optional fields.
        """
        minimal_person = {
            "@type": "Person",
            "id": "test:person:456"
        }

        result = PersonConverter.dci_person_to_individual_data(minimal_person)

        # Should return empty dict or dict with only present fields
        self.assertIsInstance(result, dict)
        self.assertNotIn('first_name', result)
        self.assertNotIn('last_name', result)

    def test_dci_person_to_individual_data_date_parsing(self):
        """
        Test date parsing in conversion.
        """
        person = {
            "birth_date": "1990-01-15T00:00:00Z"
        }

        result = PersonConverter.dci_person_to_individual_data(person)

        # Verify date is correctly parsed
        self.assertEqual(result['dob'], date(1990, 1, 15))
        self.assertIsInstance(result['dob'], date)
