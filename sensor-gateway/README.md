# Chuxin Sensor Gateway

This directory contains WebSocket gateways that provide the frontend with live
`SensorBatch` messages.

The frontend connects to:

```text
ws://localhost:18081/chuxin-vue/sensor-gateway/ws
```

or, in production behind Apache:

```text
wss://jp.jerrypsy.top/chuxin-vue/sensor-gateway/ws
```

## Message format

```json
{
  "type": "sensor_batch",
  "batch": {
    "signal": "eeg",
    "sampleRateHz": 500,
    "firstSeq": 1000,
    "startedAtMs": 1780000000000,
    "channelNames": ["CH1_processed_uV"],
    "samples": [[1.2], [1.1]],
    "rawChannelNames": ["CH1_counts", "CH1_raw_uV"],
    "rawSamples": [[13422, 1200.1], [13420, 1199.9]],
    "status": 0
  }
}
```

`channelNames` and `samples` are the user-facing display or derived metrics.
`rawChannelNames` and `rawSamples` are optional hardware-level diagnostic
fields. Gateways omit them by default to keep the early skeleton lightweight;
start a gateway with `--include-raw` when developing algorithms or diagnostics.
The intervention page intentionally does not render raw ADC/count fields.

## Mock hardware gateway

The mock gateway reads recorded hardware CSV files and emits the same
WebSocket protocol as the BLE gateway. It is used when the physical devices are
not attached, while keeping the frontend and business code on the real gateway
contract.

```bash
cd /root/jry/chuxin
python3 -m venv sensor-gateway/.venv
sensor-gateway/.venv/bin/pip install -r sensor-gateway/requirements.txt
sensor-gateway/.venv/bin/python sensor-gateway/mock_sensor_gateway.py --batch-ms 250
```

## BLE gateway

The BLE gateway ports the hardware protocol and MATLAB parsing references to
Python. It requires hardware access and the `bleak` package.

```bash
sensor-gateway/.venv/bin/python sensor-gateway/ble_sensor_gateway.py
```

Both gateway implementations emit the same WebSocket batch protocol, so the
frontend does not change when switching between recorded hardware data and real
BLE devices.

Use `--include-raw` on either gateway only when raw hardware fields are needed.
The default stream is intentionally small: display/derived channels only, 250ms
mock batches, and no raw sample payload.

See `../HARDWARE_SENSOR_GATEWAY.md` for the current hardware parsing status and
real-device integration steps.
