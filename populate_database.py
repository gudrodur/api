import pandas as pd
import asyncio
from faker import Faker
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from sqlalchemy.future import select
from setup_db import (
    User, ContactList, Sale, SaleStatus, SalesOutcome, Call, SaleContact, SessionLocal
)

# Initialize Faker
fake = Faker()

# Path to CSV file
CSV_FILE_PATH = r"C:\Users\gudro\Downloads\Thjodskra\converted_csv\national_registry.csv"

# Function to ensure timestamps are in UTC format without timezone offset issues
def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

async def insert_data():
    """Reads names & national IDs from CSV, then populates all tables in phone_sales.db."""
    try:
        # Load CSV (force column 8 to string to avoid DtypeWarning)
        df = pd.read_csv(CSV_FILE_PATH, delimiter=",", encoding="utf-8", on_bad_lines="skip", dtype={8: str})

        # ✅ Standardize column names
        df.columns = df.columns.str.strip().str.upper()

        # ✅ Limit to first 50 records
        df = df.head(50)
    except Exception as e:
        print(f"⚠ Error reading CSV: {e}")
        return

    try:
        async with SessionLocal() as session:
            # ✅ Insert Sale Statuses if they don't exist
            existing_statuses = await session.execute(select(SaleStatus.name))
            existing_statuses = {row[0] for row in existing_statuses.fetchall()}
            
            new_statuses = ["Pending", "Completed", "Cancelled"]
            statuses_to_add = [SaleStatus(name=status) for status in new_statuses if status not in existing_statuses]

            if statuses_to_add:
                session.add_all(statuses_to_add)
                await session.commit()
                print(f"✅ Added {len(statuses_to_add)} new SaleStatus records.")

            # ✅ Insert Sales Outcomes if they don't exist
            existing_outcomes = await session.execute(select(SalesOutcome.description))
            existing_outcomes = {row[0] for row in existing_outcomes.fetchall()}
            
            new_outcomes = ["Success", "Failure", "Follow-Up Required"]
            outcomes_to_add = [SalesOutcome(description=outcome) for outcome in new_outcomes if outcome not in existing_outcomes]

            if outcomes_to_add:
                session.add_all(outcomes_to_add)
                await session.commit()
                print(f"✅ Added {len(outcomes_to_add)} new SalesOutcome records.")

        async with SessionLocal() as session:
            # ✅ Insert Users (Sales agents) only if they don't exist
            existing_users = await session.execute(select(User.username))
            existing_users = {row[0] for row in existing_users.fetchall()}

            users = []
            for _, row in df.iterrows():
                full_name = row["FULL_NAME"].strip()
                username = full_name.replace(" ", "").lower()

                if username not in existing_users:
                    user = User(
                        username=username,
                        email=f"{username}@example.com",
                        full_name=full_name,
                        hashed_password=fake.password(),
                        phone=fake.phone_number(),
                        role=fake.random_element(["salesperson", "admin"]),
                        last_login=utc_now(),  # ✅ Ensure UTC timestamp
                        created_at=utc_now(),
                    )
                    users.append(user)

            if users:
                session.add_all(users)
                await session.commit()
                print(f"✅ Added {len(users)} new Users.")

        async with SessionLocal() as session:
            # ✅ Insert Contacts (Customers) only if they don't exist
            existing_contacts = await session.execute(select(ContactList.name))
            existing_contacts = {row[0] for row in existing_contacts.fetchall()}

            contacts = []
            for _, row in df.iterrows():
                full_name = row["FULL_NAME"].strip()

                if full_name not in existing_contacts:
                    contact = ContactList(
                        name=full_name,
                        phone=fake.phone_number(),
                        email=f"{full_name.replace(' ', '').lower()}@example.com",
                        age=fake.random_int(min=18, max=90),
                        status_current="Unprocessed",
                        created_at=utc_now(),  # ✅ Ensure UTC timestamp
                        updated_at=utc_now(),
                    )
                    contacts.append(contact)

            if contacts:
                session.add_all(contacts)
                await session.commit()
                print(f"✅ Added {len(contacts)} new Contacts.")

        print("✅ Database population completed successfully!")

    except IntegrityError:
        print("⚠ Skipping duplicate entries.")
    except Exception as e:
        print(f"⚠ Database error: {e}")

# ✅ Run the script
if __name__ == "__main__":
    asyncio.run(insert_data())
