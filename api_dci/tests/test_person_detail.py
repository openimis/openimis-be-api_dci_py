"""
Integration tests for DCI Person Detail API

Tests the GET /registry/person/{person_id} endpoint.
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from api_dci.tests.mixin import DCIApiTestMixin, PersonTestMixin, LogInMixin


class PersonDetailAPITestCase(DCIApiTestMixin, PersonTestMixin, LogInMixin, APITestCase):
    """
    Test cases for DCI Person Detail API endpoint.
    Tests GET /registry/person/{person_id} functionality.
    """

    base_url = "/api/api_dci/registry/person"

    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test user and authenticate
        self.test_user = self.get_or_create_user_api()
        self.login()

        # Create test Individual
        try:
            from individual.models import Individual
            from core.models import Gender

            # Get or create gender
            male_gender, _ = Gender.objects.get_or_create(code='M', defaults={'gender': 'Male'})

            # Create test individual
            self.test_individual = Individual.objects.create(
                first_name="Test",
                last_name="Person",
                dob="1990-01-15",
                gender=male_gender,
                phone="+1234567890",
                email="test.person@example.com",
                user_created=self.test_user,
                user_updated=self.test_user
            )

            # Generate person_id in openimis format
            self.person_id = f"openimis:individual:{self.test_individual.uuid}"

            self.has_individual_module = True
        except ImportError:
            self.has_individual_module = False
            self.skipTest("Individual module not available")

    def tearDown(self):
        """Clean up test data."""
        if self.has_individual_module:
            try:
                from individual.models import Individual
                Individual.objects.filter(
                    first_name="Test",
                    last_name="Person"
                ).delete()
            except:
                pass

    def test_get_person_valid_id(self):
        """Test GET person with valid person_id."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify response structure (SPDCI Person format)
        self.assertIn('identifier', response_data)
        self.assertIn('name', response_data)

        # Verify person data
        name = response_data.get('name', {})
        self.assertEqual(name.get('given_name'), "Test")
        self.assertEqual(name.get('family_name'), "Person")

    def test_get_person_invalid_id_format(self):
        """Test GET person with invalid person_id format."""
        invalid_id = "invalid-format-123"
        url = f"{self.base_url}/{invalid_id}"

        response = self.client.get(url)

        # Should return 404 or 400
        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_get_person_nonexistent_id(self):
        """Test GET person with non-existent person_id."""
        nonexistent_id = "openimis:individual:00000000-0000-0000-0000-000000000000"
        url = f"{self.base_url}/{nonexistent_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_person_response_contains_identifier(self):
        """Test that response contains proper identifier structure."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify identifier array exists
        self.assertIn('identifier', response_data)
        self.assertIsInstance(response_data['identifier'], list)
        self.assertGreater(len(response_data['identifier']), 0)

        # Verify identifier structure
        identifier = response_data['identifier'][0]
        self.assertIn('type', identifier)
        self.assertIn('value', identifier)
        self.assertIn('system', identifier)
        self.assertEqual(identifier['system'], 'openimis')

    def test_get_person_response_contains_name(self):
        """Test that response contains proper name structure."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify name structure
        self.assertIn('name', response_data)
        name = response_data['name']
        self.assertIn('given_name', name)
        self.assertIn('family_name', name)
        self.assertIn('full_name', name)

        # Verify full_name is constructed correctly
        expected_full_name = f"{self.test_individual.first_name} {self.test_individual.last_name}"
        self.assertEqual(name['full_name'], expected_full_name)

    def test_get_person_response_contains_birth_date(self):
        """Test that response contains birth_date in correct format."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify birth_date exists and is ISO format
        self.assertIn('birth_date', response_data)
        birth_date = response_data['birth_date']
        self.assertIsNotNone(birth_date)
        # Should be in ISO datetime format
        self.assertIn('T', birth_date)
        self.assertTrue(birth_date.endswith('Z'))

    def test_get_person_response_contains_sex(self):
        """Test that response contains sex in SPDCI format."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify sex enumeration
        self.assertIn('sex', response_data)
        sex = response_data['sex']
        self.assertIn(sex, ['male', 'female', 'others', 'unknown'])

    def test_get_person_response_contains_phone_number(self):
        """Test that response contains phone_number as array."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify phone_number is array
        self.assertIn('phone_number', response_data)
        phone_numbers = response_data['phone_number']
        self.assertIsInstance(phone_numbers, list)
        self.assertGreater(len(phone_numbers), 0)
        self.assertIn("+1234567890", phone_numbers)

    def test_get_person_response_contains_email(self):
        """Test that response contains email as array."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify email is array
        self.assertIn('email', response_data)
        emails = response_data['email']
        self.assertIsInstance(emails, list)
        self.assertGreater(len(emails), 0)
        self.assertIn("test.person@example.com", emails)

    def test_get_person_without_authentication(self):
        """Test GET person without authentication."""
        # Logout first
        self.client.logout()

        url = f"{self.base_url}/{self.person_id}"
        response = self.client.get(url)

        # Should require authentication
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_person_response_contains_timestamps(self):
        """Test that response contains registration and update timestamps."""
        url = f"{self.base_url}/{self.person_id}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Verify timestamps exist
        self.assertIn('registration_date', response_data)
        self.assertIn('last_updated', response_data)

        # Verify they are in ISO format
        self.assertIsNotNone(response_data['registration_date'])
        self.assertIsNotNone(response_data['last_updated'])
