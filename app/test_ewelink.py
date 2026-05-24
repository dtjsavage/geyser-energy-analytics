from ewelink_client import EWeLinkClient

client = EWeLinkClient()

devices = client.get_devices()
print(f"Found {len(devices)} devices")

for d in devices:
    print(d["name"], d["deviceid"])
