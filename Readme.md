# Manicmoddin's Car MQTT Sniffer

This application is an interface between mqtt and [lubelogger](https://lubelogger.com/).
The main idea is that an application / car will post on an MQTT topic and the relevent details will be added to lubelogger

## Lubelogger

Lubelogger is a Self-Hosted, Open source Vehicle Maintenance, Fuel and mileage tracker, more details can be found on their website above.

## CarMqttSniffer

At the time of writing, I had a car that has a smart feature where by in Home Assistant I can see the mileage of the car. I also can see the Location.

This led to the idea of reporting the mileage when  the car come home, so I have an accurate record of the trips that the car does.

## Prepwork

You should be able to just download the latest docker image form dockerhub and use the compose yaml to get this going. Be sure to rename the `.env_sample` to `.env` and set up your connections. 