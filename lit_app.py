import streamlit as st
import requests
import json
import datetime
import pandas as pd

import altair as alt
from dotenv import load_dotenv
import os
"""
# StreamLit Test App
## Weather and Sensor Data Hambrücken

"""


load_dotenv()
WEATHER_KEY = os.getenv('WEATHER')
DATACAKE_KEY = os.getenv('DATACAKE')
deviceId = os.getenv('DEVICE')


def fetch_data(date):
    url = f"https://api.weatherapi.com/v1/history.json?key={WEATHER_KEY}&q=49.185159,8.548294&dt={date}"
    response = requests.get(url)

    if response.status_code == 200:
        data_for_date = response.json()
        # Process the data to desired format
        processed_data = {
            "date": date,
            "location": data_for_date['location'],
            "forecast": {
                "forecastday": [{
                    "date": data_for_date['forecast']['forecastday'][0]['date'],
                    "day": data_for_date['forecast']['forecastday'][0]['day'],
                    "hour": data_for_date['forecast']['forecastday'][0]['hour']
                }]
            }
        }
        return processed_data
    else:
        print(
            f"Failed to retrieve data for {date}. Status Code: {response.status_code}")
        return None


def load_data_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)["weatherData"]
    except (FileNotFoundError, KeyError):
        return []


def save_data_to_file(filename, data):
    with open(filename, 'w') as file:
        json.dump({"weatherData": data}, file)


def create_dataframe_from_json(json_data):
    # Extracting only the desired fields from the nested JSON and converting it to a dataframe
    flattened_data = []
    for item in json_data:
        # Extracting core details
        date = item['date']
        location = item['location']
        forecast_day = item['forecast']['forecastday'][0]
        day_data = forecast_day['day']

        # Combine the data
        combined_data = {
            'date': date,
            'totalprecip_mm': day_data['totalprecip_mm'],
           
        }

        flattened_data.append(combined_data)

    df = pd.DataFrame(flattened_data)
    return df


def get_hourly_rain(weather_data_json):
    # Extract the hourly forecast data
    hourly_forecast = weather_data_json['weatherData'][0]['forecast']['forecastday'][0]['hour']
    
    # Create a list of dictionaries with time and precipitation data for each hour
    hourly_rain_data = [{"time": entry["time"], "precip_mm": entry["precip_mm"]} for entry in hourly_forecast]
    
    return hourly_rain_data


def get_cake_data(device):
    url = 'https://api.datacake.co/graphql/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Token {DATACAKE_KEY}"
    }

    # Get today's date
    today = datetime.date.today()

    timeRangeStart = (today - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
    timeRangeEnd = today.strftime('%Y-%m-%dT%H:%M')

    query = f"""
query {{
    device(deviceId: "{device}") {{
        history(fields: ["DISTANCE"], timerangestart: "{timeRangeStart}", timerangeend: "{timeRangeEnd}", resolution: "raw") 
    }}
}}
"""


    response = requests.post(url, json={'query': query}, headers=headers)
    return response.json()

# Ensure the response was successful
    if response.status_code == 200:
        json_response = response.json()
        print(json_response)
    else:
        print("Error:", response.status_code, response.text)


def main():
    FILENAME = "weather_data.json"
    today = datetime.date.today()
    data = load_data_from_file(FILENAME)

    for i in range(7):
        date = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        dates_in_data = [item['date'] for item in data]

        if date not in dates_in_data:
            data_for_date = fetch_data(date)
            if data_for_date:
                data.append(data_for_date)

    save_data_to_file(FILENAME, data)
    df = create_dataframe_from_json(data)

    st.write(df)
    st.caption('Data from WeatherAPI, 7 days back from today')

# Plotting temperature trends using altair with custom colors

    plot_df = df[['date', 'totalprecip_mm']].melt(
        'date', var_name='type', value_name='value')

    chart = alt.Chart(plot_df).mark_line().encode(
        x='date:T',
        y='value:Q',
        color=alt.Color('type:N', scale=alt.Scale(domain=[
                        'totalprecip_mm'], range=['blue']))
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    st.title("Sensor Data")   
    ###Get data from datacake
    deviceHistory = get_cake_data(deviceId)
    
    ### Convert to dataframe
    history_string = deviceHistory['data']['device']['history']
    history_list = json.loads(history_string)
    print(history_list)
    df2 = pd.DataFrame(history_list)
    df2['change'] = df2['DISTANCE'].diff()
    
    st.write(df2)
    st.title("Daily MM Change Visualization")



    
    
    

if __name__ == "__main__":
    main()
