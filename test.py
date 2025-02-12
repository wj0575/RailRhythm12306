import os
import json

print("Welcome to the Rail Rhythm railway timetable query tool")
if os.path.exists('city_station.json'):
    with open('city_station.json', 'r') as f1:
        city_station = json.load(f1)
for i in city_station:
    print(i, end=": ")
    for j in city_station[i]:
        print(j, end=", ")
    print()
