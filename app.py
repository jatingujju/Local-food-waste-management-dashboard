
import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Food Waste Management", layout="wide")
st.title("🍲 Food Waste Management Insights")

DB_FILE = 'food_wastage.db'

@st.cache_resource
def get_db_connection():
    if not os.path.exists(DB_FILE):
        st.error(f"Database file '{DB_FILE}' not found. Please ensure all previous steps were run correctly.")
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

def run_query(query):
    conn = get_db_connection()
    if conn:
        try:
            df = pd.read_sql_query(query, conn)
            return df
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

st.sidebar.header("Filter Options")
all_cities_query = '''
    SELECT DISTINCT City FROM Providers
    UNION
    SELECT DISTINCT Location FROM Food_Listings;
'''
all_cities_df = run_query(all_cities_query)
all_cities = ['All Cities'] + sorted(all_cities_df['City'].tolist())
selected_city = st.sidebar.selectbox("🌍 Select City to Filter Data:", all_cities)

city_filter_providers = ""
city_filter_food_listings = ""
city_filter_receivers = ""
if selected_city != 'All Cities':
    city_filter_providers = f" WHERE p.City = '{selected_city}'"
    city_filter_food_listings = f" WHERE fl.Location = '{selected_city}'"
    city_filter_receivers = f" WHERE r.City = '{selected_city}'"

st.header("📍 Food Providers & Receivers")
st.subheader("1. Providers & Receivers per City")
q1 = run_query(f'''
SELECT
    p.City,
    COUNT(DISTINCT p.Provider_ID) AS Providers_Count,
    COUNT(DISTINCT r.Receiver_ID) AS Receivers_Count
FROM Providers p
LEFT JOIN Receivers r ON p.City = r.City
{city_filter_providers}
GROUP BY p.City
ORDER BY Providers_Count DESC, Receivers_Count DESC;
''')
if not q1.empty:
    st.dataframe(q1, use_container_width=True)
    st.bar_chart(q1.set_index("City")[["Providers_Count", "Receivers_Count"]])
else:
    st.info(f"No data for selected city: {selected_city}.")

st.subheader("2. Provider Type Contribution")
q2_where = f"WHERE City = '{selected_city}'" if selected_city != 'All Cities' else ""
q2 = run_query(f'''
SELECT Type AS Provider_Type, COUNT(*) AS Total
FROM Providers
{q2_where}
GROUP BY Type
ORDER BY Total DESC;
''')
if not q2.empty:
    st.dataframe(q2, use_container_width=True)
    st.bar_chart(q2.set_index("Provider_Type"))
else:
    st.info(f"No provider type data for selected city: {selected_city}.")

st.subheader("3. Provider Contacts")
if selected_city != 'All Cities':
    q3 = run_query(f"SELECT Name, Contact FROM Providers WHERE City = '{selected_city}';")
    if not q3.empty:
        st.dataframe(q3, use_container_width=True)
    else:
        st.info(f"No providers found in {selected_city}.")
else:
    st.info("Select a specific city from the dropdown to view provider contacts.")

st.subheader("4. Top 5 Receivers by Claims Count")
q4_where = f"AND r.City = '{selected_city}'" if selected_city != 'All Cities' else ""
q4 = run_query(f'''
SELECT r.Name AS Receiver_Name, COUNT(c.Claim_ID) AS Claims_Count
FROM Claims c
JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
{q4_where}
GROUP BY r.Name
ORDER BY Claims_Count DESC
LIMIT 5;
''')
if not q4.empty:
    st.dataframe(q4, use_container_width=True)
    st.bar_chart(q4.set_index("Receiver_Name"))
else:
    st.info(f"No receiver claims data for selected city: {selected_city}.")

st.header("📦 Food Listings & Availability")
st.subheader("5. Total Food Quantity in Listings")
q5_where = f"WHERE Location = '{selected_city}'" if selected_city != 'All Cities' else ""
q5 = run_query(f'''
SELECT SUM(Quantity) AS Total_Food_Quantity FROM Food_Listings
{q5_where};
''')
if not q5.empty and q5.iloc[0]['Total_Food_Quantity'] is not None:
    st.dataframe(q5, use_container_width=True)
else:
    st.info(f"No food listings quantity data for selected city: {selected_city}.")

st.subheader("6. City with Highest Food Listings")
st.info("This metric shows the city with the highest listings overall, not filtered by selection.")
q6 = run_query('''
SELECT Location AS City, COUNT(*) AS Listing_Count
FROM Food_Listings
GROUP BY Location
ORDER BY Listing_Count DESC
LIMIT 1;
''')
st.dataframe(q6, use_container_width=True)

st.subheader("7. Most Common Food Types Listed")
q7_where = f"WHERE Location = '{selected_city}'" if selected_city != 'All Cities' else ""
q7 = run_query(f'''
SELECT Food_Type, COUNT(*) AS Count
FROM Food_Listings
{q7_where}
GROUP BY Food_Type
ORDER BY Count DESC;
''')
if not q7.empty:
    st.dataframe(q7, use_container_width=True)
    st.bar_chart(q7.set_index("Food_Type"))
else:
    st.info(f"No food type data for selected city: {selected_city}.")

st.header("📊 Claims & Distribution")
st.subheader("8. Claims Count per Food Item (Top 10)")
q8_where = f"AND fl.Location = '{selected_city}'" if selected_city != 'All Cities' else ""
q8 = run_query(f'''
SELECT fl.Food_Name, COUNT(c.Claim_ID) AS Total_Claims
FROM Claims c
JOIN Food_Listings fl ON c.Food_ID = fl.Food_ID
{q8_where}
GROUP BY fl.Food_Name
ORDER BY Total_Claims DESC
LIMIT 10;
''')
if not q8.empty:
    st.dataframe(q8, use_container_width=True)
    st.bar_chart(q8.set_index("Food_Name"))
else:
    st.info(f"No claims per food item data for selected city: {selected_city}.")

st.subheader("9. Top Provider by Successful Claims (Top 10)")
q9_where = f"AND p.City = '{selected_city}'" if selected_city != 'All Cities' else ""
q9 = run_query(f'''
SELECT p.Name AS Provider_Name, COUNT(c.Claim_ID) AS Successful_Claims_Count
FROM Claims c
JOIN Food_Listings fl ON c.Food_ID = fl.Food_ID
JOIN Providers p ON fl.Provider_ID = p.Provider_ID
WHERE c.Status = 'Completed'
{q9_where}
GROUP BY p.Name
ORDER BY Successful_Claims_Count DESC
LIMIT 10;
''')
if not q9.empty:
    st.dataframe(q9, use_container_width=True)
    st.bar_chart(q9.set_index("Provider_Name"))
else:
    st.info(f"No successful claims data for selected city: {selected_city}.")

st.subheader("10. Claims Status Distribution (Percentage)")
st.info("This shows overall claims status and is not filtered by city selection.")
q10 = run_query('''
SELECT Status,
       ROUND((COUNT(*) * 100.0) / (SELECT COUNT(*) FROM Claims), 2) AS Percentage
FROM Claims
GROUP BY Status;
''')
st.dataframe(q10, use_container_width=True)
st.bar_chart(q10.set_index("Status"))

st.header("📈 Analysis & Insights")
st.subheader("11. Average Quantity Claimed per Receiver (Top 10)")
q11_where = f"AND r.City = '{selected_city}'" if selected_city != 'All Cities' else ""
q11 = run_query(f'''
SELECT r.Name AS Receiver_Name, ROUND(AVG(fl.Quantity), 2) AS Avg_Quantity_Claimed
FROM Claims c
JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
JOIN Food_Listings fl ON c.Food_ID = fl.Food_ID
WHERE c.Status = 'Completed'
{q11_where}
GROUP BY r.Name
ORDER BY Avg_Quantity_Claimed DESC
LIMIT 10;
''')
if not q11.empty:
    st.dataframe(q11, use_container_width=True)
else:
    st.info(f"No average quantity claimed data for selected city: {selected_city}.")

st.subheader("12. Most Claimed Meal Type")
q12_where = f"AND fl.Location = '{selected_city}'" if selected_city != 'All Cities' else ""
q12 = run_query(f'''
SELECT fl.Meal_Type, COUNT(c.Claim_ID) AS Claim_Count
FROM Claims c
JOIN Food_Listings fl ON c.Food_ID = fl.Food_ID
{q12_where}
GROUP BY fl.Meal_Type
ORDER BY Claim_Count DESC
LIMIT 1;
''')
if not q12.empty:
    st.dataframe(q12, use_container_width=True)
else:
    st.info(f"No most claimed meal type data for selected city: {selected_city}.")

st.subheader("13. Total Quantity Donated by Each Provider (Top 10)")
q13_where = f"AND p.City = '{selected_city}'" if selected_city != 'All Cities' else ""
q13 = run_query(f'''
SELECT p.Name AS Provider_Name, SUM(fl.Quantity) AS Total_Quantity_Donated
FROM Providers p
JOIN Food_Listings fl ON p.Provider_ID = fl.Provider_ID
{q13_where}
GROUP BY p.Name
ORDER BY Total_Quantity_Donated DESC
LIMIT 10;
''')
if not q13.empty:
    st.dataframe(q13, use_container_width=True)
    st.bar_chart(q13.set_index("Provider_Name"))
else:
    st.info(f"No total quantity donated data for selected city: {selected_city}.")
