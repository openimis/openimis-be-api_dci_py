import os
import random
import uuid
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from individual.models import Individual
from core.models import User

# Disable opensearch autosync at module level
os.environ['OPENSEARCH_DSL_AUTOSYNC'] = 'False'

# --------------------------- Reference data ---------------------------

FIRST_NAMES_MALE = [
    "John", "Bob", "Charlie", "Edward", "George", "Igor", "Kevin", "Michael",
    "Oscar", "Quinn", "Samuel", "David", "James", "Robert", "William",
    "Thomas", "Daniel", "Joseph", "Henry", "Ahmed", "Omar", "Yusuf",
    "Emmanuel", "Jean", "Pierre", "Carlos", "Luis", "Raj", "Amit", "Wei",
]

FIRST_NAMES_FEMALE = [
    "Jane", "Alice", "Diana", "Fiona", "Hannah", "Julia", "Laura", "Nina",
    "Paula", "Rose", "Sarah", "Mary", "Emma", "Olivia", "Sophia",
    "Isabella", "Amina", "Fatima", "Aisha", "Marie", "Ana", "Priya",
    "Lakshmi", "Mei", "Hana", "Grace", "Ruth", "Esther", "Martha", "Agnes",
]

LAST_NAMES = [
    "Doe", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson",
    "Nguyen", "Kumar", "Singh", "Ali", "Mohamed", "Chen", "Wang", "Kim",
    "Okafor", "Diallo", "Traore", "Nkosi", "Mwangi", "Banda", "Phiri",
]

GENDERS = ["Male", "Female"]
MARITAL_STATUSES = ["single", "married", "divorced", "widowed", "separated"]
IDENTIFIER_TYPES = ["NationalID", "PassportNumber", "BirthCertificate", "FarmerID", "SocialSecurityNumber"]
NAME_PREFIXES = ["Mr.", "Mrs.", "Ms.", "Dr.", ""]
NAME_SUFFIXES = ["Jr.", "Sr.", "II", "III", ""]
PHONE_PREFIXES = ["+1", "+44", "+91", "+254", "+256", "+260", "+233", "+234", "+66", "+84"]

# --- Social Registry specific ---
STREET_ADDRESSES = [
    "123 Main St", "456 Oak Ave", "789 Market Rd", "12 River Lane",
    "55 Park Blvd", "90 Church St", "34 Hill Rd", "67 Lake Dr",
    "22 Forest Path", "8 Valley View", "101 Farm Rd", "15 Temple St",
    "300 Kings Way", "42 Queens Rd", "78 Station Rd",
]

CITIES = [
    "Nairobi", "Kampala", "Lusaka", "Accra", "Lagos", "Dar es Salaam",
    "Addis Ababa", "Kigali", "Lilongwe", "Maputo", "Harare", "Bamako",
    "Dakar", "Dhaka", "Kathmandu", "Phnom Penh", "Vientiane", "Hanoi",
    "Lima", "Bogota", "Quito", "La Paz", "Guatemala City", "San Salvador",
]

COUNTRIES = [
    "Kenya", "Uganda", "Zambia", "Ghana", "Nigeria", "Tanzania",
    "Ethiopia", "Rwanda", "Malawi", "Mozambique", "Zimbabwe", "Mali",
    "Senegal", "Bangladesh", "Nepal", "Cambodia", "Laos", "Vietnam",
    "Peru", "Colombia", "Ecuador", "Bolivia", "Guatemala", "El Salvador",
]

POSTAL_CODES = [f"{random.randint(10000, 99999)}" for _ in range(50)]
EDUCATION_LEVELS = ["none", "primary", "secondary", "vocational", "tertiary", "bachelor", "master", "doctorate"]
EMPLOYMENT_STATUSES = ["employed", "self-employed", "unemployed", "retired", "student", "homemaker", "casual_labor"]
OCCUPATIONS = ["farmer", "teacher", "trader", "artisan", "driver", "health_worker", "construction_worker", "domestic_worker", "fisher", "herder", "government_employee", "NGO_worker", "daily_laborer", "none"]
INCOME_LEVELS = ["very_low", "low", "medium", "high"]
LANGUAGE_CODES = ["eng", "fra", "swa", "amh", "hau", "yor", "zul", "ara", "hin", "ben", "urd", "tam", "spa", "por", "vie", "khm"]
POVERTY_SCORE_TYPES = ["income-based", "asset-based", "multidimensional", "consumption-based"]

# --- Farmer Registry specific ---
FARM_TYPES = ["Small subsistence-oriented farms", "Medium commercial farms", "Large commercial farms", "Small mixed farms", "Pastoral farms", "Cooperative farms"]
CROP_ACTIVITY_GROUPS = ["annual crops", "perennial crops", "vegetable crops"]
CROP_TYPES = ["Cereals", "Fruit and nuts", "Vegetables", "Root crops", "Pulses", "Oil-bearing crops", "Sugar crops", "Fibre crops", "Spice crops", "Tobacco"]
CROP_VARIETIES = ["local", "hybrid", "improved", "traditional", "organic"]
SEASONS = ["winter", "summer", "rainy", "dry", "all-year"]
END_USES = ["Food for human consumption", "Animal feed", "Industrial use", "Export", "Seed production", "Biofuel"]
IRRIGATION_WATER_SOURCES = ["Surface water", "Groundwater", "Rainwater", "Mixed surface water and groundwater", "Recycled water"]
FERTILIZER_TYPES = ["Organic fertilizers", "Chemical fertilizers", "Bio-fertilizers", "Compost", "Green manure", "None"]
ANIMAL_TYPES = ["Cattle", "Sheep and goats", "Pigs", "Poultry", "Horses and donkeys", "Camels", "Rabbits", "Bees"]
LIVESTOCK_SYSTEMS = ["Extensive system", "Intensive system", "Mixed system", "Nomadic system", "Semi-intensive system"]
AGRI_SUPPORT_ACTIVITIES = ["Support activities for crop production", "Support activities for animal production", "Post-harvest crop activities", "Seed processing for propagation", "Agricultural extension services"]
AQUA_SUPPORT_ACTIVITIES = ["Support activities for fishing and aquaculture", "Marine fishing", "Freshwater fishing", "Fish processing"]
AQUACULTURE_TYPES = ["Marine aquafarming", "Freshwater aquafarming", "Shrimp farming", "Fish pond culture"]
MACHINERY_TYPES = ["Machine powered equipment", "Hand tools", "Animal-drawn equipment", "Irrigation equipment", "Harvesting equipment", "Processing equipment"]
EQUIPMENT_SOURCES = ["Owned", "Rented", "Provided by a cooperative", "Provided by government", "Shared with neighbors", "Borrowed"]
PLACE_NAMES = ["Koh Samui", "Nakhon Ratchasima", "Chiang Mai", "Udon Thani", "Kampala District", "Masaka", "Jinja", "Mbarara", "Nairobi County", "Kisumu", "Mombasa", "Nakuru", "Lusaka Province", "Copperbelt", "Southern Province", "Eastern Province", "Dhaka Division", "Chittagong", "Rajshahi", "Sylhet", "Punjab", "Maharashtra", "Tamil Nadu", "Karnataka"]

# --------------------------- Helpers ----------------------------------

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_iso_datetime(start_year=2020, end_year=2025):
    d = random_date(date(start_year, 1, 1), date(end_year, 12, 31))
    return datetime(d.year, d.month, d.day, random.randint(0, 23), 0, 0).isoformat() + "Z"

def random_phone():
    prefix = random.choice(PHONE_PREFIXES)
    number = "".join([str(random.randint(0, 9)) for _ in range(9)])
    return f"{prefix}{number}"

def random_email(first_name, last_name, index):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "farmer.org", "agri.net", "mail.co"]
    return f"{first_name.lower()}.{last_name.lower()}{index}@{random.choice(domains)}"

def random_geo():
    return {
        "@type": "spdci:GeoLocation",
        "latitude": round(random.uniform(-30, 40), 4),
        "longitude": round(random.uniform(-20, 120), 4),
    }

def generate_identifier(id_type=None):
    id_type = id_type or random.choice(IDENTIFIER_TYPES)
    prefix_map = {"NationalID": "N", "PassportNumber": "P", "BirthCertificate": "BC", "FarmerID": "F", "SocialSecurityNumber": "SSN"}
    value = f"{prefix_map.get(id_type, 'X')}{random.randint(100000, 999999)}"
    return {"identifier_type": id_type, "identifier_value": value}

def generate_address():
    country = random.choice(COUNTRIES)
    idx = COUNTRIES.index(country)
    city = CITIES[idx] if idx < len(CITIES) else random.choice(CITIES)
    return {"@type": "Address", "street_address": random.choice(STREET_ADDRESSES), "city": city, "postal_code": random.choice(POSTAL_CODES), "country": country}

def generate_place():
    return {"@type": "Place", "name": random.choice(PLACE_NAMES), "geo": random_geo(), "address": generate_address()}

def pick_name(gender):
    if gender == "Male":
        return random.choice(FIRST_NAMES_MALE), random.choice(LAST_NAMES)
    return random.choice(FIRST_NAMES_FEMALE), random.choice(LAST_NAMES)

def generate_sr_person(first_name, last_name, gender, dob):
    sex = "male" if gender == "Male" else "female"
    return {"@type": "SRPerson", "identifier": [generate_identifier(), generate_identifier()], "name": {"given_name": first_name, "surname": last_name, "prefix": random.choice(NAME_PREFIXES), "suffix": random.choice(NAME_SUFFIXES)}, "sex": sex, "birth_date": dob.isoformat() + "T00:00:00Z", "address": generate_address(), "registration_date": random_iso_datetime(2018, 2023)}

def generate_sr_member(gender=None):
    gender = gender or random.choice(GENDERS)
    first_name, last_name = pick_name(gender)
    dob = random_date(date(1950, 1, 1), date(2015, 12, 31))
    return {"@type": "Member", "member_identifier": [generate_identifier()], "demographic_info": generate_sr_person(first_name, last_name, gender, dob), "is_disabled": random.random() < 0.1, "marital_status": random.choice(MARITAL_STATUSES), "registration_date": random_iso_datetime(2018, 2023)}

def generate_sr_group(first_name, last_name, gender, dob):
    group_size = random.randint(1, 8)
    reg_date = random_iso_datetime(2018, 2023)
    head_id = generate_identifier()
    return {"@type": "Group", "group_identifier": [generate_identifier("NationalID")], "group_type": "family", "place": generate_place(), "poverty_score": round(random.uniform(0, 100), 1), "poverty_score_type": random.choice(POVERTY_SCORE_TYPES), "group_head_info": {"@type": "Member", "member_identifier": [head_id], "demographic_info": generate_sr_person(first_name, last_name, gender, dob), "is_disabled": random.random() < 0.05, "marital_status": random.choice(MARITAL_STATUSES), "registration_date": reg_date}, "group_size": group_size, "member_list": [generate_sr_member() for _ in range(max(0, group_size - 1))], "registration_date": reg_date, "last_updated": random_iso_datetime(2023, 2025), "additional_attributes": generate_additional_attributes()}

def generate_additional_attributes():
    attrs = []
    if random.random() < 0.7: attrs.append({"key": "education_level", "value": random.choice(EDUCATION_LEVELS)})
    if random.random() < 0.7: attrs.append({"key": "employment_status", "value": random.choice(EMPLOYMENT_STATUSES)})
    if random.random() < 0.6: attrs.append({"key": "occupation", "value": random.choice(OCCUPATIONS)})
    if random.random() < 0.5: attrs.append({"key": "income_level", "value": random.choice(INCOME_LEVELS)})
    if random.random() < 0.4: attrs.append({"key": "language_code", "value": random.choice(LANGUAGE_CODES)})
    return attrs

def build_social_json_ext(first_name, last_name, gender, dob, index):
    member_id = generate_identifier()
    reg_date = random_iso_datetime(2018, 2023)
    return {"reg_record_type": "SRPerson", "reg_type": "ns:org:RegistryType:Social", "member_identifier": member_id, "demographic_info": generate_sr_person(first_name, last_name, gender, dob), "gender": gender, "phone": random_phone(), "email": random_email(first_name, last_name, index), "address": generate_address(), "education_level": random.choice(EDUCATION_LEVELS), "employment_status": random.choice(EMPLOYMENT_STATUSES), "occupation": random.choice(OCCUPATIONS), "income_level": random.choice(INCOME_LEVELS), "language_code": random.sample(LANGUAGE_CODES, k=random.randint(1, 3)), "is_disabled": random.random() < 0.1, "marital_status": random.choice(MARITAL_STATUSES), "group_details": generate_sr_group(first_name, last_name, gender, dob), "registration_date": reg_date, "last_updated": random_iso_datetime(2023, 2025), "additional_attributes": generate_additional_attributes()}

def generate_crop_production():
    crops = []
    for _ in range(random.randint(1, 3)):
        crops.append({"activity_group": random.choice(CROP_ACTIVITY_GROUPS), "crop_type": random.choice(CROP_TYPES), "variety": random.choice(CROP_VARIETIES), "season": random.choice(SEASONS), "end_use": random.sample(END_USES, k=random.randint(1, 3)), "irrigation": random.choice([True, False]), "irrigation_water": random.sample(IRRIGATION_WATER_SOURCES, k=random.randint(1, 2)), "fertilizer_type": random.sample(FERTILIZER_TYPES, k=random.randint(1, 2)), "registration_date": random_iso_datetime(2020, 2023), "last_updated": random_iso_datetime(2023, 2025)})
    return crops

def generate_animal_production():
    if random.random() < 0.3: return []
    animals = []
    for _ in range(random.randint(1, 2)):
        animals.append({"type": random.choice(ANIMAL_TYPES), "count": random.randint(1, 200), "livestock_system": random.choice(LIVESTOCK_SYSTEMS), "registration_date": random_iso_datetime(2020, 2023), "last_updated": random_iso_datetime(2023, 2025)})
    return animals

def generate_farming_activities():
    activities = []
    for _ in range(random.randint(1, 2)):
        activity = {"crop_production": generate_crop_production(), "animal_production": generate_animal_production(), "mixed_farming": random.choice([True, False]), "agri_support_activities": random.sample(AGRI_SUPPORT_ACTIVITIES, k=random.randint(0, 2)), "registration_date": random_iso_datetime(2020, 2023), "last_updated": random_iso_datetime(2023, 2025)}
        if random.random() < 0.2:
            activity["aqua_support_activities"] = random.choice(AQUA_SUPPORT_ACTIVITIES)
            activity["aqua_culture"] = random.sample(AQUACULTURE_TYPES, k=random.randint(1, 2))
        activities.append(activity)
    return activities

def generate_farm_details():
    farms = []
    for _ in range(random.randint(1, 3)):
        farms.append({"place": {"name": random.choice(PLACE_NAMES), "geo": random_geo()}, "farm_type": random.choice(FARM_TYPES), "farming_activities": generate_farming_activities(), "registration_date": random_iso_datetime(2020, 2023), "last_updated": random_iso_datetime(2023, 2025)})
    return farms

def generate_machineries_details():
    if random.random() < 0.4: return []
    machines = []
    for _ in range(random.randint(1, 3)):
        machines.append({"type": random.choice(MACHINERY_TYPES), "count": random.randint(1, 10), "equipement_source": random.choice(EQUIPMENT_SOURCES), "registration_date": random_iso_datetime(2020, 2023), "last_updated": random_iso_datetime(2023, 2025)})
    return machines

def generate_fr_family_details(first_name, last_name, gender, dob):
    group_size = random.randint(1, 8)
    reg_date = random_iso_datetime(2018, 2023)
    head_id = generate_identifier()
    def fr_member(g=None):
        g = g or random.choice(GENDERS)
        fn, ln = pick_name(g)
        return {"member_identifier": [generate_identifier()], "demographic_info": {"spdci:identifier": [generate_identifier()], "name": {"given_name": fn, "surname": ln, "prefix": random.choice(NAME_PREFIXES), "suffix": random.choice(NAME_SUFFIXES)}, "sex": g.lower(), "birth_date": random_date(date(1950, 1, 1), date(2015, 12, 31)).isoformat() + "T00:00:00Z", "registration_date": random_iso_datetime(2020, 2023)}, "is_disabled": random.random() < 0.1, "marital_status": random.choice(MARITAL_STATUSES), "registration_date": random_iso_datetime(2020, 2023)}
    return {"group_identifier": [generate_identifier("FarmerID")], "group_type": "family", "poverty_score": round(random.uniform(0, 100), 1), "poverty_score_type": random.choice(POVERTY_SCORE_TYPES), "group_head_info": {"member_identifier": [head_id], "demographic_info": {"identifier": head_id, "name": {"first_name": first_name, "last_name": last_name}, "date_of_birth": dob.isoformat() + "T00:00:00Z", "gender": gender}, "is_disabled": random.random() < 0.05, "marital_status": random.choice(MARITAL_STATUSES), "registration_date": reg_date}, "group_size": group_size, "member_list": [fr_member() for _ in range(max(0, group_size - 1))], "registration_date": reg_date, "last_updated": random_iso_datetime(2023, 2025)}

def build_farmer_json_ext(first_name, last_name, gender, dob, index):
    member_id = generate_identifier()
    reg_date = random_iso_datetime(2018, 2023)
    return {"reg_record_type": "spdci-extensions-dci:Farmer", "reg_type": "ns:org:RegistryType:FR", "famer_personal_details": {"member_identifier": member_id, "demographic_info": {"identifier": member_id, "name": {"first_name": first_name, "last_name": last_name}, "date_of_birth": dob.isoformat() + "T00:00:00Z", "gender": gender}}, "gender": gender, "phone": random_phone(), "email": random_email(first_name, last_name, index), "family_details": generate_fr_family_details(first_name, last_name, gender, dob), "farm_details": generate_farm_details(), "machineries_details": generate_machineries_details(), "registration_date": reg_date, "last_updated": random_iso_datetime(2023, 2025)}

REGISTRY_BUILDERS = {"social": build_social_json_ext, "farmer": build_farmer_json_ext}

# --------------------------- Command ----------------------------------

class Command(BaseCommand):
    help = 'Seed SPDCI-compliant individuals (Social/Farmer) into openIMIS'

    def add_arguments(self, parser):
        parser.add_argument(
            "--registry", "-r",
            choices=["social", "farmer"],
            default="social",
            help="Registry type: social (SRPerson) or farmer (FRPerson). Default: social",
        )
        parser.add_argument(
            "-n", "--count",
            type=int,
            default=10,
            help="Number of individuals to seed. Default: 10",
        )

    def handle(self, *args, **options):
        registry = options['registry']
        count = options['count']
        
        builder = REGISTRY_BUILDERS.get(registry)
        user = (
            User.objects.filter(username='Admin').first()
            or User.objects.filter(username='admin').first()
            or User.objects.first()
        )
        
        if not user:
            self.stderr.write("Error: No user found in the database.")
            return

        reg_label = "Social Registry (SRPerson)" if registry == "social" else "Farmer Registry (FRPerson)"
        self.stdout.write(f"Seeding {count} individuals for {reg_label}...")

        start_date = date(1950, 1, 1)
        end_date = date(2010, 12, 31)
        created_count = 0

        with transaction.atomic():
            for i in range(count):
                try:
                    gender = random.choice(GENDERS)
                    f_name, l_name = pick_name(gender)
                    dob = random_date(start_date, end_date)
                    json_ext = builder(f_name, l_name, gender, dob, i)

                    individual = Individual(
                        first_name=f_name,
                        last_name=l_name,
                        dob=dob,
                        json_ext=json_ext,
                    )
                    individual.save(username=user.username)
                    created_count += 1

                    if (i + 1) % 100 == 0:
                        self.stdout.write(f"  Progress: {i + 1}/{count} ...")
                except Exception as e:
                    self.stderr.write(f"  Failed at index {i}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} {reg_label} records."))
