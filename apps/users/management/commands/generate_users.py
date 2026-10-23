# from django.core.management.base import BaseCommand
# from faker import Faker

# from apps.users.models import User


# class Command(BaseCommand):
#     help = "Generate Faker users directly in the database."

#     def add_arguments(self, parser):
#         parser.add_argument(
#             "--count",
#             type=int,
#             default=1000,
#             help="Number of users to generate.",
#         )

#         parser.add_argument(
#             "--batch-size",
#             type=int,
#             default=1000,
#             help="Number of users inserted per batch.",
#         )

#         parser.add_argument(
#             "--password",
#             type=str,
#             default="admin@123",
#             help="Password assigned to generated users.",
#         )

#     def handle(self, *args, **options):
#         count = options["count"]
#         batch_size = options["batch_size"]
#         password = options["password"]

#         if count <= 0:
#             self.stdout.write(
#                 self.style.ERROR(
#                     "count must be greater than 0."
#                 )
#             )
#             return

#         if batch_size <= 0:
#             self.stdout.write(
#                 self.style.ERROR(
#                     "batch-size must be greater than 0."
#                 )
#             )
#             return

#         fake = Faker()

#         users = []

#         self.stdout.write(
#             f"Generating {count:,} users..."
#         )

#         for index in range(1, count + 1):
#             email = fake.unique.email()
#             username = fake.unique.user_name()

#             created_at = fake.date_time_this_decade(
#                 tzinfo=None
#             )

#             updated_at = fake.date_time_between(
#                 start_date=created_at,
#                 end_date="now",
#                 tzinfo=None,
#             )

#             profile = {
#                 "metadata": {
#                     "version": fake.numerify(
#                         "#.#.##"
#                     ),
#                     "createdAt": created_at.isoformat(),
#                     "updatedAt": updated_at.isoformat(),
#                     "accountStatus": "active",
#                     "accountTier": fake.random_element(
#                         elements=[
#                             "standard",
#                             "premium",
#                             "vip",
#                         ]
#                     ),
#                     "role": "user",
#                     "is_active": True,
#                     "schema_version": "1.0.0",
#                 },

#                 "personal": {
#                     "prefix": fake.prefix(),
#                     "firstName": fake.first_name(),
#                     "middle": fake.first_name(),
#                     "lastName": fake.last_name(),
#                     "suffix": fake.suffix(),
#                     "displayName": fake.name(),
#                     "dob": fake.date_of_birth().isoformat(),
#                     "gender": fake.random_element(
#                         elements=[
#                             "male",
#                             "female",
#                             "non-binary",
#                         ]
#                     ),
#                     "genderType": fake.random_element(
#                         elements=[
#                             "male",
#                             "female",
#                             "other",
#                         ]
#                     ),
#                     "zodiac": fake.random_element(
#                         elements=[
#                             "Aries",
#                             "Taurus",
#                             "Gemini",
#                             "Cancer",
#                             "Leo",
#                             "Virgo",
#                             "Libra",
#                             "Scorpio",
#                             "Sagittarius",
#                             "Capricorn",
#                             "Aquarius",
#                             "Pisces",
#                         ]
#                     ),
#                     "bio": fake.sentence(),
#                     "avatar": fake.image_url(),
#                 },

#                 "contact": {
#                     "email": email,
#                     "username": username,
#                     "secondaryEmail": fake.email(),
#                     "phone": (
#                         f"({fake.numerify('###')}) "
#                         f"{fake.numerify('###')}-"
#                         f"{fake.numerify('####')}"
#                     ),
#                     "fax": (
#                         f"{fake.numerify('###')}-"
#                         f"{fake.numerify('###')}-"
#                         f"{fake.numerify('####')}"
#                     ),
#                     "website": fake.url(),
#                 },

#                 "location": {
#                     "address": fake.street_address(),
#                     "secondaryAddress": fake.secondary_address(),
#                     "state": fake.state(),
#                     "city": fake.city(),
#                     "zip": fake.zipcode(),
#                     "country": fake.country(),
#                     "countryCode": fake.country_code(),
#                     "continent": fake.random_element(
#                         elements=[
#                             "Africa",
#                             "Asia",
#                             "Europe",
#                             "North America",
#                             "South America",
#                             "Oceania",
#                         ]
#                     ),
#                     "timezone": fake.timezone(),
#                     "latitude": str(
#                         fake.latitude()
#                     ),
#                     "longitude": str(
#                         fake.longitude()
#                     ),
#                 },

#                 "professional": {
#                     "jobTitle": fake.job(),
#                     "jobDescriptor": fake.word(),
#                     "jobArea": fake.word(),
#                     "jobType": fake.random_element(
#                         elements=[
#                             "Full-time",
#                             "Part-time",
#                             "Contract",
#                             "Temporary",
#                             "Internship",
#                         ]
#                     ),
#                     "company": {
#                         "name": fake.company(),
#                         "catchPhrase": fake.catch_phrase(),
#                         "bs": fake.bs(),
#                         "industry": fake.word(),
#                     },
#                 },

#                 "financial": {
#                     "currency": fake.currency_name(),
#                     "currencyCode": fake.currency_code(),
#                     "currencySymbol": fake.currency_symbol(),
#                     "iban": fake.iban(),
#                     "bic": fake.bban(),
#                     "accountNumber": fake.bban(),
#                     "routingNumber": fake.numerify(
#                         "#########"
#                     ),
#                     "creditCard": {
#                         "issuer": fake.credit_card_provider(),
#                         "number": fake.credit_card_number(),
#                         "cvv": fake.credit_card_security_code(),
#                         "pin": fake.numerify("####"),
#                         "expiration": fake.credit_card_expire(),
#                     },
#                 },

#                 "network": {
#                     "ipAddress": fake.ipv4(),
#                     "ipv6": fake.ipv6(),
#                     "macAddress": fake.mac_address(),
#                     "userAgent": fake.user_agent(),
#                     "domain": fake.domain_name(),
#                 },

#                 "preferences": {
#                     "color": fake.color_name(),
#                     "colorHex": fake.hex_color(),
#                     "language": fake.language_name(),
#                     "theme": fake.random_element(
#                         elements=[
#                             "light",
#                             "dark",
#                             "system",
#                         ]
#                     ),
#                     "notificationsEnabled": fake.boolean(),
#                 },

#                 "assets": {
#                     "vehicle": {
#                         "model": fake.vehicle.model(),
#                         "manufacturer": fake.vehicle.manufacturer(),
#                         "type": fake.vehicle.type(),
#                         "fuel": fake.vehicle.fuel(),
#                         # "fuel": fake.random_element(
#                         #     elements=[
#                         #         "Gasoline",
#                         #         "Diesel",
#                         #         "Electric",
#                         #         "Hybrid",
#                         #     ]
#                         # ),
#                         "vrm": fake.vehicle.vrm() // 'MF56UPA',
#                         "vin": fake.vehicle.vin(),
#                         "color": fake.vehicle.color(),
#                         "year": str(fake.random_int(1950, 2026)),
#                     }
#                 },
#             }

#             user = User(
#                 email=email,
#                 username=username,
#                 role="user",
#                 account_status="active",
#                 schema_version="1.0.0",
#                 is_active=True,
#                 profile=profile,
#             )

#             user.set_password(password)

#             users.append(user)

#             if len(users) >= batch_size:
#                 User.objects.bulk_create(
#                     users,
#                     batch_size=batch_size,
#                 )

#                 self.stdout.write(
#                     f"Inserted {index:,}/{count:,}"
#                 )

#                 users.clear()

#         if users:
#             User.objects.bulk_create(
#                 users,
#                 batch_size=batch_size,
#             )

#         self.stdout.write(
#             self.style.SUCCESS(
#                 f"Successfully generated {count:,} users."
#             )
#         )

from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from faker import Faker

from apps.users.models import User


class Command(BaseCommand):
    help = "Generate Faker users directly in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1_000,
            help="Number of users to generate.",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=1_000,
            help="Number of users inserted per batch.",
        )

        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Optional fixed password for every generated user.",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def js_date(value: datetime) -> str:
        """
        Convert datetime to the format used by the generated JSON data.
        """
        value = value.replace(tzinfo=timezone.utc)

        return value.strftime(
            "%a %b %d %Y %H:%M:%S GMT+0000 "
            "(Coordinated Universal Time)"
        )

    @staticmethod
    def semver(fake: Faker) -> str:
        """
        Equivalent to:
            {{faker 'system.semver'}}
        """
        return (
            f"{fake.random_int(0, 9)}."
            f"{fake.random_int(0, 99)}."
            f"{fake.random_int(0, 99)}"
        )

    @staticmethod
    def phone_number(fake: Faker) -> str:
        """
        Generate a phone number without Faker extensions such as x1234.
        """
        return (
            f"({fake.numerify('###')}) "
            f"{fake.numerify('###')}-"
            f"{fake.numerify('####')}"
        )

    @staticmethod
    def fax_number(fake: Faker) -> str:
        """
        Generate a fax number without an extension.
        """
        return (
            f"{fake.numerify('###')}-"
            f"{fake.numerify('###')}-"
            f"{fake.numerify('####')}"
        )

    @staticmethod
    def zodiac(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "Aries",
                "Taurus",
                "Gemini",
                "Cancer",
                "Leo",
                "Virgo",
                "Libra",
                "Scorpio",
                "Sagittarius",
                "Capricorn",
                "Aquarius",
                "Pisces",
            ]
        )

    @staticmethod
    def role(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "user",
                "admin",
                "manager",
                "moderator",
            ]
        )

    @staticmethod
    def account_status(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "pending",
                "active",
                "suspended",
                "banned",
                "archived",
            ]
        )

    @staticmethod
    def account_tier(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "standard",
                "premium",
                "vip",
            ]
        )

    @staticmethod
    def gender(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "male",
                "female",
            ]
        )

    @staticmethod
    def gender_type(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "male",
                "female",
            ]
        )

    @staticmethod
    def job_type(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "Full-time",
                "Part-time",
                "Contract",
                "Internship",
                "Freelance",
            ]
        )

    @staticmethod
    def theme(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "light",
                "dark",
                "system",
            ]
        )

    @staticmethod
    def continent(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "Africa",
                "Asia",
                "Europe",
                "North America",
                "South America",
                "Oceania",
                "Antarctica",
            ]
        )

    @staticmethod
    def fuel(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "Gasoline",
                "Diesel",
                "Electric",
                "Hybrid",
            ]
        )

    @staticmethod
    def credit_card_issuer(fake: Faker) -> str:
        return fake.random_element(
            elements=[
                "visa",
                "mastercard",
                "amex",
                "jcb",
                "discover",
            ]
        )

    @staticmethod
    def vehicle_year(fake: Faker) -> str:
        return str(
            fake.random_int(
                min=1990,
                max=2026,
            )
        )

    # ------------------------------------------------------------------
    # User generation
    # ------------------------------------------------------------------

    def generate_user(self, fake: Faker, password: str) -> User:
        email = fake.unique.email()
        username = fake.unique.user_name()

        created_at = fake.date_time_this_decade()

        updated_at = fake.date_time_between(
            start_date=created_at,
            end_date="now",
        )

        account_status = self.account_status(fake)

        # Keep database authentication state consistent
        # with account status.
        is_active = account_status not in {
            "banned",
            "suspended",
            "archived",
        }

        role = self.role(fake)
        account_tier = self.account_tier(fake)

        schema_version = self.semver(fake)

        metadata = {
            "version": self.semver(fake),
            "createdAt": self.js_date(created_at),
            "updatedAt": self.js_date(updated_at),
            "accountStatus": account_status,
            "accountTier": account_tier,
            "role": role,
            "is_active": is_active,
            "schema_version": schema_version,
        }

        personal = {
            "prefix": fake.random_element(
                elements=[
                    "Mr.",
                    "Ms.",
                    "Mrs.",
                    "Dr.",
                ]
            ),
            "firstName": fake.first_name(),
            "middle": fake.first_name(),
            "lastName": fake.last_name(),
            "suffix": fake.random_element(
                elements=[
                    "",
                    "Jr.",
                    "Sr.",
                    "PhD",
                    "MD",
                ]
            ),
            "displayName": fake.name(),
            "dob": fake.date_of_birth().strftime(
                "%a %b %d %Y %H:%M:%S GMT+0000 "
                "(Coordinated Universal Time)"
            ),
            "gender": self.gender(fake),
            "genderType": self.gender_type(fake),
            "zodiac": self.zodiac(fake),
            "bio": fake.sentence(),
            "avatar": fake.image_url(),
        }

        contact = {
            "email": email,
            "username": username,
            "secondaryEmail": fake.email(),
            "phone": self.phone_number(fake),
            "fax": self.fax_number(fake),
            "website": fake.url(),
        }

        location = {
            "address": fake.street_address(),
            "secondaryAddress": fake.secondary_address(),
            "state": fake.state(),
            "city": fake.city(),
            "zip": fake.zipcode(),
            "country": fake.country(),
            "countryCode": fake.country_code(),
            "continent": self.continent(fake),
            "timezone": fake.timezone(),
            "latitude": str(fake.latitude()),
            "longitude": str(fake.longitude()),
        }

        professional = {
            "jobTitle": fake.job(),
            "jobDescriptor": fake.word(),
            "jobArea": fake.word(),
            "jobType": self.job_type(fake),
            "company": {
                "name": fake.company(),
                "catchPhrase": fake.catch_phrase(),
                "bs": fake.bs(),
                "industry": fake.word(),
            },
        }

        financial = {
            "currency": fake.currency_name(),
            "currencyCode": fake.currency_code(),
            "currencySymbol": fake.currency_symbol(),
            "iban": fake.iban(),
            "bic": fake.swift(),
            "accountNumber": fake.bban(),
            "routingNumber": fake.numerify("#########"),
            "creditCard": {
                "issuer": self.credit_card_issuer(fake),
                "number": fake.credit_card_number(),
                "cvv": fake.credit_card_security_code(),
                "pin": fake.numerify("####"),
                "expiration": fake.credit_card_expire(),
            },
        }

        network = {
            "ipAddress": fake.ipv4(),
            "ipv6": fake.ipv6(),
            "macAddress": fake.mac_address(),
            "userAgent": fake.user_agent(),
            "domain": fake.domain_name(),
        }

        preferences = {
            "color": fake.color_name(),
            "colorHex": fake.hex_color(),
            "language": fake.language_name(),
            "theme": self.theme(fake),
            "notificationsEnabled": fake.boolean(),
        }

        assets = {
            "vehicle": {
                "model": fake.word(),
                "manufacturer": fake.company(),
                "type": fake.word(),
                "fuel": self.fuel(fake),
                "vin": fake.vin(),
                "color": fake.color_name(),
                "month": fake.date_object().strftime("%m"),
                "year": self.vehicle_year(fake),
            }
        }

        profile = {
            "metadata": metadata,
            "personal": personal,
            "contact": contact,
            "location": location,
            "professional": professional,
            "financial": financial,
            "network": network,
            "preferences": preferences,
            "assets": assets,
        }

        user = User(
            email=email,
            username=username,
            role=role,
            account_status=account_status,
            schema_version=schema_version,
            is_active=is_active,
            profile=profile,
        )

        user.set_password(password)

        return user

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        count = options["count"]
        batch_size = options["batch_size"]
        # fixed_password = options["password"]

        if count <= 0:
            raise ValueError(
                "count must be greater than 0"
            )

        if batch_size <= 0:
            raise ValueError(
                "batch-size must be greater than 0"
            )

        fake = Faker()

        # Optional fixed password for test datasets.
        # password = fixed_password or fake.password(
        #     length=16,
        #     special_chars=True,
        #     digits=True,
        #     upper_case=True,
        #     lower_case=True,
        # )

        password = "admin@123"
        self.stdout.write(
            f"Generating {count:,} users..."
        )

        users = []

        for index in range(1, count + 1):
            user = self.generate_user(
                fake,
                password,
            )

            users.append(user)

            if len(users) >= batch_size:
                User.objects.bulk_create(
                    users,
                    batch_size=batch_size,
                )

                self.stdout.write(
                    f"Inserted {index:,}/{count:,}"
                )

                users.clear()

        if users:
            User.objects.bulk_create(
                users,
                batch_size=batch_size,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated "
                f"{count:,} users."
            )
        )