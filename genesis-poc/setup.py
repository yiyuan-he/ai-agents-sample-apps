import os
import shutil
import sqlite3

import pandas as pd
import requests

class CustomerSupportSetup:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(CustomerSupportSetup, cls).__new__(cls)
            cls._instance.create_resource()
        return cls._instance

    def create_resource(self, overwrite_setup = False):
        print("Setting up customer support database...")
        db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
        local_file = "travel2.sqlite"
        # The backup lets us restart for each tutorial section
        self.backup_file = "travel2.backup.sqlite"
    
        if overwrite_setup or not os.path.exists(local_file):
            response = requests.get(db_url)
            response.raise_for_status()  # Ensure the request was successful
            with open(local_file, "wb") as f:
                f.write(response.content)
            # Backup - we will use this to "reset" our DB in each section
            shutil.copy(local_file, self.backup_file)

        self.db = self.update_dates(local_file)

    def get_db(self):
        return self.db

    # Convert the flights to present time for our tutorial
    def update_dates(self, file):
        shutil.copy(self.backup_file, file)
        conn = sqlite3.connect(file)
        cursor = conn.cursor()

        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        ).name.tolist()
        tdf = {}
        for t in tables:
            tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

        example_time = pd.to_datetime(
            tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
        ).max()
        current_time = pd.to_datetime("now").tz_localize(example_time.tz)
        time_diff = current_time - example_time

        tdf["bookings"]["book_date"] = (
            pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
            + time_diff
        )

        datetime_columns = [
            "scheduled_departure",
            "scheduled_arrival",
            "actual_departure",
            "actual_arrival",
        ]
        for column in datetime_columns:
            tdf["flights"][column] = (
                pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
            )

        for table_name, df in tdf.items():
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        del df
        del tdf
        conn.commit()
        conn.close()

        return file


# Example usage (testing the graph without Streamlit):
if __name__ == "__main__":
    CustomerSupportSetup()
    