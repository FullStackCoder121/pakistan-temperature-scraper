import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm
import os

# URL for Max Temperature
url = "https://nwfc.pmd.gov.pk/new/max-temp.php"

# Session Setup
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# Step 1: Fetch station list
res = session.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
stations = soup.select("select[name='station'] option")
station_list = [(opt['value'], opt.text.strip()) for opt in stations if opt['value'].isdigit()]

# Step 2: Data list
temp_data = []

# Step 3: Scrape each station
print("\n🌡️ Scraping Max Temperature Data...\n")
for station_id, station_name in tqdm(station_list, desc="🔍 Scraping", unit="station"):
    payload = {
        'station': station_id,
        'filter': 'station'
    }

    try:
        response = session.post(url, data=payload, timeout=10)
        page = BeautifulSoup(response.text, 'html.parser')
        table = page.find("table", class_="table table-bordered")

        if table:
            rows = table.find_all("tr")[1:]  # skip header row
            for row in rows:
                cols = row.find_all("td")
                if len(cols) == 4:
                    province = cols[0].text.strip()
                    reported_station = cols[1].text.strip()
                    temp = cols[2].text.strip()
                    date = cols[3].text.strip()

                    record = {
                        'Station ID': station_id,
                        'Station Name': station_name,
                        'Province': province,
                        'Reported Station': reported_station,
                        'Max Temp (°C)': temp,
                        'Date': date
                    }

                    temp_data.append(record)

                    # 👇 Live output
                    print(f"{record['Station ID']}, {record['Station Name']}, {record['Province']}, "
                          f"{record['Reported Station']}, {record['Max Temp (°C)']}, {record['Date']}")

    except Exception as e:
        print(f"❌ Error scraping {station_name}: {e}")

    time.sleep(0.5)

# Step 4: Create DataFrame
new_df = pd.DataFrame(temp_data)

# Step 5: Merge with old CSV if exists
csv_file = "pakistan_temperature_data.csv"
if os.path.exists(csv_file):
    old_df = pd.read_csv(csv_file)
    combined_df = pd.concat([old_df, new_df], ignore_index=True)
else:
    combined_df = new_df

# Step 6: Clean up
combined_df['Date'] = pd.to_datetime(combined_df['Date'], errors='coerce', dayfirst=True)
combined_df.drop_duplicates(inplace=True)
combined_df = combined_df.sort_values(by='Date', ascending=False)

# Step 7: Save
combined_df.to_csv(csv_file, index=False)

print("\n✅ Temperature scraping completed!")
print(f"📁 Updated file: {csv_file}\n")
