"""
DCI Person Converter

Converts between openIMIS Individual model and SPDCI-compliant
Social Registry (SRPerson) or Farmer Registry (FRPerson) format.

The Individual model stores most SPDCI fields inside json_ext.
This converter reads them back out and structures the response
exactly as the SPDCI async/sync search specs require.
"""
from datetime import datetime


class PersonConverter:
    """
    Converter for openIMIS Individual -> SPDCI registry record.
    """

    # ------------------------------------------------------------------ #
    #  Public entry point                                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def individual_to_dci_person(individual, registry_type=None):
        """
        Convert an openIMIS Individual to the SPDCI search-response
        reg_record format.

        Args:
            individual: openIMIS Individual model instance
            registry_type: "social" or "farmer". Falls back to app config.

        Returns:
            dict – one element suitable for the reg_records array.
        """
        if registry_type is None:
            from ..apps import ApiDciConfig
            registry_type = ApiDciConfig.registry_type

        ext = individual.json_ext or {}

        if registry_type == "farmer":
            return PersonConverter._build_farmer_record(individual, ext)
        return PersonConverter._build_social_record(individual, ext)

    # ------------------------------------------------------------------ #
    #  Social Registry (SRPerson / Group)                                 #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_social_record(individual, ext):
        """Build a Social Registry Group record with the individual as head."""
        group = ext.get("group_details", {})

        record = {
            "@type": "Group",
            "group_identifier": group.get("group_identifier", [
                _make_identifier("NationalID", individual.uuid)
            ]),
            "group_type": group.get("group_type", "family"),
            "place": group.get("place", _fallback_place(ext)),
            "poverty_score": group.get("poverty_score", ext.get("poverty_score")),
            "poverty_score_type": group.get("poverty_score_type", ext.get("poverty_score_type")),
            "group_head_info": PersonConverter._build_sr_member(individual, ext, is_head=True),
            "group_size": group.get("group_size", 1),
            "member_list": group.get("member_list", []),
            "registration_date": ext.get("registration_date", _iso_or_none(individual.date_created)),
            "last_updated": ext.get("last_updated", _iso_or_none(individual.date_updated)),
            "additional_attributes": ext.get("additional_attributes", []),
        }
        return record

    @staticmethod
    def _build_sr_member(individual, ext, is_head=False):
        """Build a Social Registry Member block."""
        demo = ext.get("demographic_info", {})
        member_id = ext.get("member_identifier")
        if not member_id:
            member_id = _make_identifier("NationalID", individual.uuid)

        member = {
            "@type": "Member",
            "member_identifier": [member_id] if isinstance(member_id, dict) else member_id if isinstance(member_id, list) else [member_id],
            "demographic_info": PersonConverter._build_sr_person(individual, ext, demo),
            "is_disabled": ext.get("is_disabled", False),
            "marital_status": ext.get("marital_status", ""),
            "registration_date": ext.get("registration_date", _iso_or_none(individual.date_created)),
        }
        return member

    @staticmethod
    def _build_sr_person(individual, ext, demo):
        """Build the SRPerson demographic_info block."""
        name_block = demo.get("name", {})
        person = {
            "@type": "SRPerson",
            "identifier": demo.get("identifier", [
                _make_identifier("NationalID", individual.uuid)
            ]),
            "name": {
                "given_name": name_block.get("given_name", individual.first_name or ""),
                "surname": name_block.get("surname", individual.last_name or ""),
                "prefix": name_block.get("prefix", ""),
                "suffix": name_block.get("suffix", ""),
            },
            "sex": demo.get("sex", _resolve_sex(individual, ext)),
            "birth_date": demo.get("birth_date", individual.dob.isoformat() + "T00:00:00Z" if individual.dob else None),
            "address": demo.get("address", ext.get("address", {})),
            "registration_date": demo.get("registration_date", ext.get("registration_date")),
        }
        return person

    # ------------------------------------------------------------------ #
    #  Farmer Registry (FRPerson)                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_farmer_record(individual, ext):
        """Build a Farmer Registry record."""
        personal = ext.get("famer_personal_details", {})
        demo = personal.get("demographic_info", {})

        record = {
            "@type": "spdci-extensions-dci:Farmer",
            "famer_personal_details": {
                "member_identifier": personal.get("member_identifier",
                    _make_identifier("FarmerID", individual.uuid)),
                "demographic_info": {
                    "identifier": demo.get("identifier",
                        _make_identifier("FarmerID", individual.uuid)),
                    "name": demo.get("name", {
                        "first_name": individual.first_name or "",
                        "last_name": individual.last_name or "",
                    }),
                    "date_of_birth": demo.get("date_of_birth",
                        individual.dob.isoformat() + "T00:00:00Z" if individual.dob else None),
                    "gender": demo.get("gender", ext.get("gender", "")),
                },
            },
            "family_details": ext.get("family_details", {}),
            "farm_details": ext.get("farm_details", []),
            "machineries_details": ext.get("machineries_details", []),
            "registration_date": ext.get("registration_date", _iso_or_none(individual.date_created)),
            "last_updated": ext.get("last_updated", _iso_or_none(individual.date_updated)),
        }
        return record

    # ------------------------------------------------------------------ #
    #  Reverse: DCI -> Individual data (unchanged from original)          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def dci_person_to_individual_data(dci_person):
        """
        Convert DCI Person to openIMIS Individual data.
        """
        data = {}
        if "firstName" in dci_person:
            data["first_name"] = dci_person["firstName"]
        if "lastName" in dci_person:
            data["last_name"] = dci_person["lastName"]
        if "dob" in dci_person:
            data["dob"] = datetime.fromisoformat(dci_person["dob"]).date()
        if "gender" in dci_person:
            gender_reverse_map = {'Male': 'M', 'Female': 'F', 'Other': 'O'}
            data["gender_code"] = gender_reverse_map.get(dci_person["gender"], 'O')
        if "phone" in dci_person:
            data["phone"] = dci_person["phone"]
        if "email" in dci_person:
            data["email"] = dci_person["email"]
        return data


# ====================================================================== #
#  Helpers                                                                #
# ====================================================================== #

def _make_identifier(id_type, uuid_val):
    return {"identifier_type": id_type, "identifier_value": str(uuid_val)}


def _iso_or_none(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat() + "Z"
    return str(dt)


def _resolve_sex(individual, ext):
    """Try to resolve sex from ext, model, or gender field."""
    if ext.get("gender"):
        return ext["gender"].lower() if ext["gender"] in ("Male", "Female") else ext["gender"]
    if hasattr(individual, 'gender') and individual.gender:
        code = individual.gender.code if hasattr(individual.gender, 'code') else individual.gender
        return {"M": "male", "F": "female"}.get(code, "")
    return ""


def _fallback_place(ext):
    """Build a minimal place from address if no group place is available."""
    addr = ext.get("address", {})
    if addr:
        return {"@type": "Place", "address": addr}
    return {}
