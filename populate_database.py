import pandas as pd
import asyncio
from faker import Faker
import logging
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from sqlalchemy.future import select
from sale_crm.main import (
    UserDB, ContactList, SaleDB, SaleStatus, SalesOutcomes, CallDB, SaleContact
)
from setup_db import SessionLocal  # Keep SessionLocal from setup_db


# Initialize Faker
fake = Faker()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Path to CSV file
CSV_FILE_PATH = r"C:\Users\gudro\Downloads\Thjodskra\converted_csv\national_registry.csv"

# Ensure timestamps are in UTC
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

async def insert_data():
    """Reads names & national IDs from CSV, then populates all tables in PostgreSQL."""
    try:
        df = pd.read_csv(CSV_FILE_PATH, delimiter=",", encoding="utf-8", on_bad_lines="skip", dtype={8: str})
        df.columns = df.columns.str.strip().str.upper()  # ✅ Standardize column names
        df = df.head(50)  # ✅ Limit to first 50 records
    except Exception as e:
        logger.error(f"⚠ Error reading CSV: {e}")
        return

    try:
        async with SessionLocal() as session:
            # ✅ Insert Sale Statuses if missing
            result = await session.execute(select(SaleStatus.name))
            existing_statuses = set(result.scalars().all())

            new_statuses = ["Pending", "Completed", "Cancelled"]
            statuses_to_add = [SaleStatus(name=status) for status in new_statuses if status not in existing_statuses]

            if statuses_to_add:
                session.add_all(statuses_to_add)
                await session.commit()
                logger.info("✅ Added %d new SaleStatus records.", len(statuses_to_add))

            # ✅ Insert Sales Outcomes if missing
            result = await session.execute(select(SalesOutcomes.description))
            existing_outcomes = set(result.scalars().all())

            new_outcomes = ["Success", "Failure", "Follow-Up Required"]
            outcomes_to_add = [SalesOutcomes(description=outcome) for outcome in new_outcomes if outcome not in existing_outcomes]

            if outcomes_to_add:
                session.add_all(outcomes_to_add)
                await session.commit()
                logger.info("✅ Added %d new SalesOutcomes records.", len(outcomes_to_add))

        async with SessionLocal() as session:
            # ✅ Insert Users if missing
            result = await session.execute(select(UserDB.username))
            existing_users = set(result.scalars().all())

            users = []
            for _, row in df.iterrows():
                full_name = row["FULL_NAME"].strip()
                username = full_name.replace(" ", "").lower()

                if username not in existing_users:
                    users.append(UserDB(
                        username=username,
                        email=f"{username}@example.com",
                        full_name=full_name,
                        hashed_password=fake.password(),
                        phone=fake.phone_number(),
                        role=fake.random_element(["salesperson", "admin"]),
                        last_login=utc_now(),
                        created_at=utc_now(),
                    ))

            if users:
                session.add_all(users)
                await session.commit()
                logger.info("✅ Added %d new Users.", len(users))

        async with SessionLocal() as session:
            # ✅ Insert Contacts if missing
            result = await session.execute(select(ContactList.name))
            existing_contacts = set(result.scalars().all())

            contacts = []
            for _, row in df.iterrows():
                full_name = row["FULL_NAME"].strip()

                if full_name not in existing_contacts:
                    contacts.append(ContactList(
                        name=full_name,
                        phone=fake.phone_number(),
                        email=f"{full_name.replace(' ', '').lower()}@example.com",
                        age=fake.random_int(min=18, max=90),
                        status_current="Unprocessed",
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    ))

            if contacts:
                session.add_all(contacts)
                await session.commit()
                logger.info("✅ Added %d new Contacts.", len(contacts))

        logger.info("✅ Database population completed successfully!")

    except IntegrityError:
        logger.warning("⚠ Skipping duplicate entries.")
    except Exception as e:
        logger.error(f"⚠ Database error: {e}")

# ✅ Run the script
if __name__ == "__main__":
    asyncio.run(insert_data())
