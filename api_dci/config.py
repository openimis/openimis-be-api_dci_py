"""
DCI API Configuration

Configuration for SPDCI registry type and behavior.
"""
import os


# ============================================
# SPDCI REGISTRY TYPE CONFIGURATION
# ============================================

# SPDCI Registry Type - determines response format
# Options: 'fr' (Farmer Registry), 'sr' (Social Registry), 'ibr' (Beneficiary Registry)
# This should be set via environment variable SPDCI_REGISTRY_TYPE
# Default: 'fr' (Farmer Registry)
SPDCI_REGISTRY_TYPE = os.environ.get('SPDCI_REGISTRY_TYPE', 'fr').lower()

# Registry type display names
REGISTRY_TYPES = {
    'fr': {
        'name': 'Farmer Registry',
        'short_name': 'FR',
        'record_type': 'Farmer',
        'reg_type': 'ns:org:RegistryType:FR',
        'description': 'SPDCI Farmer Registry (FR) v1.0.0 compliant',
    },
    'sr': {
        'name': 'Social Registry',
        'short_name': 'SR',
        'record_type': 'Member',
        'reg_type': 'ns:org:RegistryType:SR',
        'description': 'SPDCI Social Registry (SR) v1.0.0 compliant',
    },
    'ibr': {
        'name': 'Integrated Beneficiary Registry',
        'short_name': 'IBR',
        'record_type': 'Person',
        'reg_type': 'ns:org:RegistryType:IBR',
        'description': 'SPDCI Integrated Beneficiary Registry (IBR) v1.0.0 compliant',
    },
}


def get_registry_type():
    """
    Get the current registry type configuration.

    Returns:
        str: Registry type ('fr', 'sr', or 'ibr')
    """
    registry_type = SPDCI_REGISTRY_TYPE

    # Validate registry type
    if registry_type not in REGISTRY_TYPES:
        raise ValueError(
            f"Invalid SPDCI_REGISTRY_TYPE: {registry_type}. "
            f"Must be one of: {', '.join(REGISTRY_TYPES.keys())}"
        )

    return registry_type


def get_registry_config():
    """
    Get the configuration for the current registry type.

    Returns:
        dict: Registry configuration
    """
    registry_type = get_registry_type()
    return REGISTRY_TYPES[registry_type]


def get_registry_name():
    """Get the full name of the current registry type."""
    return get_registry_config()['name']


def get_registry_short_name():
    """Get the short name of the current registry type."""
    return get_registry_config()['short_name']


def get_record_type():
    """Get the record type for the current registry."""
    return get_registry_config()['record_type']


def get_reg_type_value():
    """Get the reg_type value for the current registry."""
    return get_registry_config()['reg_type']
