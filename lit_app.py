import streamlit as st
import requests
import json
import datetime
import pandas as pd
import altair as alt

"""
# StreamLit Test App
## Weather and Sensor Data Hambrücken
### Raw Weather Data
"""


def fetch_data(date):
    url = f"https://api.weatherapi.com/v1/history.json?key=b5731f3595a743b780a102447230708&q=49.185159,8.548294&dt={date}"
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
                    "day": data_for_date['forecast']['forecastday'][0]['day']
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

            'maxtemp_c': day_data['maxtemp_c'],
            'mintemp_c': day_data['mintemp_c'],
            'avgtemp_c': day_data['avgtemp_c'],
            'totalprecip_mm': day_data['totalprecip_mm'],
            'avghumidity': day_data['avghumidity'],
            'uv': day_data['uv']
        }

        flattened_data.append(combined_data)

    df = pd.DataFrame(flattened_data)
    return df


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
    
### Plotting temperature trends using altair with custom colors
    """
### Chart temperature
"""

    plot_df = df[['date', 'mintemp_c', 'avgtemp_c', 'maxtemp_c']].melt(
        'date', var_name='type', value_name='value')


    chart = alt.Chart(plot_df).mark_line().encode(
        x='date:T',
        y='value:Q',
        color=alt.Color('type:N', scale=alt.Scale(domain=[
                        'mintemp_c', 'avgtemp_c', 'maxtemp_c'], range=['blue', 'green', 'red']))
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    main()
