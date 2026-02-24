"""
DCI Person Converter

Converts between DCI Person schema and OpenIMIS Individual model.
"""
from datetime import datetime


class PersonConverter:
    """
    Converter for DCI Person <-> OpenIMIS Individual
    """
    
    @staticmethod
    def individual_to_dci_person(individual):
        """
        Convert OpenIMIS Individual to DCI Person format
        
        Args:
            individual: OpenIMIS Individual model instance
            
        Returns:
            dict: DCI Person object
        """
        person = {
            "@type": "Person",
            "id": f"openimis:individual:{individual.uuid}",
        }
        
        # Basic fields
        if individual.first_name:
            person["firstName"] = individual.first_name
        if individual.last_name:
            person["lastName"] = individual.last_name
        if individual.dob:
            person["dob"] = individual.dob.isoformat()
            
        # Gender mapping
        if individual.gender:
            gender_map = {
                'M': 'Male',
                'F': 'Female',
                'O': 'Other'
            }
            person["gender"] = gender_map.get(individual.gender.code, 'Other')
            
        # Contact information
        if hasattr(individual, 'phone') and individual.phone:
            person["phone"] = individual.phone
        if hasattr(individual, 'email') and individual.email:
            person["email"] = individual.email
            
        return person
    
    @staticmethod
    def dci_person_to_individual_data(dci_person):
        """
        Convert DCI Person to OpenIMIS Individual data
        
        Args:
            dci_person: DCI Person dict
            
        Returns:
            dict: Data suitable for Individual model
        """
        data = {}
        
        # Basic fields
        if "firstName" in dci_person:
            data["first_name"] = dci_person["firstName"]
        if "lastName" in dci_person:
            data["last_name"] = dci_person["lastName"]
        if "dob" in dci_person:
            # Parse ISO date string to date object
            data["dob"] = datetime.fromisoformat(dci_person["dob"]).date()
            
        # Gender mapping (reverse)
        if "gender" in dci_person:
            gender_reverse_map = {
                'Male': 'M',
                'Female': 'F',
                'Other': 'O'
            }
            data["gender_code"] = gender_reverse_map.get(dci_person["gender"], 'O')
            
        # Contact information
        if "phone" in dci_person:
            data["phone"] = dci_person["phone"]
        if "email" in dci_person:
            data["email"] = dci_person["email"]
            
        return data