import json
import mysql.connector

# Assuming you have established a MySQL connection and have a cursor object
# mydb = mysql.connector.connect(...)
# cursor = mydb.cursor()

mydb = mysql.connector.connect(
    host="localhost",
    user="pi",
    password="pi",
    database="greenhouse_db"
)

json_data = """
{
    "thresLog": [["1", "26.7"], ["2", "26.7"], ["3", "26.7"]],
    "weatherLog": [["31.57", "71%", "Clouds"]],
    "pumpLog1": {"2023-05-19": 48, "2023-05-20": 33},
    "pumpLog2": {"2023-05-19": 2},
    "pumpLog3": {"2023-05-19": 1},
    "moistureLog1": [[1006, "2023-05-18T14:39:13"], [1009, "2023-05-18T14:39:19"], [1009, "2023-05-18T14:39:25"], [1009, "2023-05-18T14:39:55"], [1009, "2023-05-18T14:40:01"]],
    "moistureLog2": [[383, "2023-05-18T14:41:01"], [383, "2023-05-18T14:41:07"], [384, "2023-05-18T14:41:13"], [383, "2023-05-18T14:41:19"], [383, "2023-05-18T14:41:25"]],
    "moistureLog3": [[339, "2023-05-18T14:41:02"], [339, "2023-05-18T14:41:07"], [338, "2023-05-18T14:41:13"], [337, "2023-05-18T14:41:19"], [337, "2023-05-18T14:41:25"]]
}
"""

# Load JSON data
data = json.loads(json_data)

# Define table names
table_names = {
    "thresLog": "water_thres_log",
    "weatherLog": "weather_log",
    "pumpLog1": "pump_log1",
    "pumpLog2": "pump_log2",
    "pumpLog3": "pump_log3",
    "moistureLog1": "moisture_log1",
    "moistureLog2": "moisture_log2",
    "moistureLog3": "moisture_log3"
}

# Iterate over each key-value pair in the JSON data
for table_name, table_data in data.items():
    if isinstance(table_data, dict):
        # For tables with dictionary data (pumpLog1, pumpLog2, pumpLog3)
        for date, value in table_data.items():
            # Check if the date already exists in the table
            query = f"SELECT COUNT(*) FROM {table_names[table_name]} WHERE date_column = %s"
            cursor.execute(query, (date,))
            count = cursor.fetchone()[0]

            if count > 0:
                # Date exists, update the value
                query = f"UPDATE {table_names[table_name]} SET value_column = %s WHERE date_column = %s"
                cursor.execute(query, (value, date))
            else:
                # Date doesn't exist, insert a new row
                query = f"INSERT INTO {table_names[table_name]} (value_column, date_column) VALUES (%s, %s)"
                cursor.execute(query, (value, date))

    elif isinstance(table_data, list):
        # For tables with list data (thresLog, weatherLog, moistureLog1, moistureLog2, moistureLog3)
        for row in table_data:
            if table_name.startswith("moistureLog"):
                # For moistureLog tables, insert a new row
                query = f"INSERT INTO {table_names[table_name]} (value_column, date_column) VALUES (%s, %s)"
                cursor.execute(query, (row[0], row[1]))
            else:
                # For thresLog and weatherLog tables, update the values
                query = f"UPDATE {table_names[table_name]} SET value1_column = %s WHERE value2_column = %s"
                cursor.execute(query, (row[0], row[1]))

# Commit the changes and close the cursor
mydb.commit()
cursor.close()
