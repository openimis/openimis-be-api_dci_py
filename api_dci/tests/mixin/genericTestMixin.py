"""
Generic Test Mixin for DCI tests

Provides base test utilities and setup for all DCI tests.
"""
from abc import ABC
from django.test import TestCase


class GenericTestMixin(TestCase, ABC):
    """
    Base test mixin for all DCI tests.
    Provides common setup and utilities.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for all tests.
        This is called once for the entire test class.
        """
        super(GenericTestMixin, cls).setUpTestData()
        # Add common test data setup here
        # For example: create test users, test locations, etc.

    def create_test_individual(self):
        """
        Create a test Individual instance.
        To be implemented by subclasses.
        """
        raise NotImplementedError("`create_test_individual()` must be implemented.")

    def verify_individual(self, individual):
        """
        Verify an Individual instance.
        To be implemented by subclasses.
        """
        raise NotImplementedError("`verify_individual()` must be implemented.")

    def create_test_dci_person(self):
        """
        Create a test DCI Person dict.
        To be implemented by subclasses.
        """
        raise NotImplementedError("`create_test_dci_person()` must be implemented.")

    def verify_dci_person(self, dci_person):
        """
        Verify a DCI Person dict.
        To be implemented by subclasses.
        """
        raise NotImplementedError("`verify_dci_person()` must be implemented.")
