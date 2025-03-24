from traffic_mafia_bot import TGTraffic
# comment for push
data, directions = "data.csv", "jsons/directions.json"

if __name__ == '__main__':
    trafficMafia = TGTraffic(data, directions)
    trafficMafia.run()
