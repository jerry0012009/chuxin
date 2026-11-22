# 硬件传感器解析与接入说明

本文档说明当前 Chuxin 项目对脑电、心率/血氧、皮肤电硬件数据的解析现状，以及后续接入真实硬件时应如何落地。目标是让前端和上层功能始终只面对稳定的 WebSocket 数据协议，硬件来源可以在网关层切换。

## 资料位置

硬件协议、测试采集样本及 MATLAB 代码都在 `hardware/` 目录。Mock 网关直接读取解包后的 CSV，无需再解压同目录的 `.rar`：

```text
hardware/EEG_8CH 通信协议.docx
hardware/PPG_GSR_BLE_通信协议.docx
hardware/EEG+GSR+PPG_test_data & matlab_code/data解释.docx
hardware/EEG+GSR+PPG_test_data & matlab_code/matlab_code/
hardware/EEG+GSR+PPG_test_data & matlab_code/*.csv
hardware/EEG+GSR+PPG_test_data & matlab_code/*.mat
```

其中：

- `EEG_8CH 通信协议.docx` 定义 EEG BLE 设备、命令、33 字节数据包、ADS1299 counts 解析和 uV 换算。
- `PPG_GSR_BLE_通信协议.docx` 定义 PPG/GSR BLE 设备、命令、71 字节批量包、PPG RED/IR 和 GSR 换算。
- `data解释.docx` 说明示例 CSV 字段含义、采样率和 MATLAB 输出。
- `matlab_code/` 是硬件调试阶段的原始解析和绘图参考。

## 当前代码结构

实时传感器链路由 Python 网关和前端 WebSocket 数据源组成：

```text
sensor-gateway/sensor_protocol.py       # 统一 WebSocket batch 协议
sensor-gateway/mock_sensor_gateway.py   # 使用已录制硬件 CSV 驱动同一套 WS 协议
sensor-gateway/ble_sensor_gateway.py    # 真实 BLE 设备解析入口
sensor-gateway/signal_processing.py     # EEG 展示用轻量处理
frontend/src/sensors/GatewaySensorSource.ts
frontend/src/components/sensors/RealtimeSignalPanel.vue
```

当前生产服务 `chuxin-sensor-gateway.service` 运行的是 `mock_sensor_gateway.py`。它不是前端 CSV 读取逻辑，而是一个完整的 WebSocket 硬件网关模拟器：数据来自 `hardware/` 中的真实采集 CSV，输出协议与真实 BLE 网关一致。

后续接真实设备时，前端不需要改。只需要让 systemd 启动 `ble_sensor_gateway.py`，并给它正确的 BLE 地址或设备名。

## 统一 WebSocket 协议

前端只消费 `sensor_batch` 消息：

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

字段约定：

- `signal`：`eeg`、`ppg` 或 `gsr`。
- `sampleRateHz`：该 batch 对应信号的采样率，EEG 500Hz，PPG 100Hz，GSR 10Hz。
- `firstSeq`：该 batch 第一个样本的硬件序号或块序号。
- `startedAtMs`：网关启动或采集启动时间，用于前端粗略状态展示，不作为硬件采样时间。
- `channelNames/samples`：前端展示和普通业务逻辑默认使用的稳定字段。
- `rawChannelNames/rawSamples`：可选的硬件原始字段，用于后续算法、记录和诊断；默认不通过 WebSocket 发送，避免骨架阶段占用过多网络、JSON 和浏览器内存资源。需要调试时用 `--include-raw` 打开。
- `status`：硬件状态字节，目前主要来自 PPG/GSR 协议。

真实 BLE 网关按硬件包节奏输出。Mock 网关默认每 250ms 输出一个较大的 batch，以减少常驻进程和浏览器的唤醒次数；采样率本身不变：

| 信号 | 采样率 | 每批样本数 | 展示字段 |
| --- | ---: | ---: | --- |
| EEG | 500Hz | Mock 默认 125；BLE 50 | `CH1_processed_uV` 到 `CH8_processed_uV` |
| PPG | 100Hz | Mock 默认 25；BLE 10 | `HR_bpm`, `SpO2_pct`, `SpO2_RatioR` |
| GSR | 10Hz | Mock 默认 2 或 3；BLE 1 | `GSR_display_mV`, `GSR_display_V`, `GSR_physical_mV`, `GSR_physical_V` |

这样做可以避免浏览器每个采样点触发一次响应式更新，资源占用更低，也更接近真实硬件网关的批量处理方式。

## EEG 解析现状

硬件信息：

- BLE 设备名：`EEG_8CH`
- Service UUID：`6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- 写命令 Characteristic：`6E400002-B5A3-F393-E0A9-E50E24DCCA9E`
- Notify Characteristic：`6E400003-B5A3-F393-E0A9-E50E24DCCA9E`
- 开始采集命令：`AA 31 55`
- 停止采集命令：`AA 32 55`
- 采样率：500Hz
- 通道数：8

数据包格式为固定 33 字节：

```text
AA 83 SEQ_L SEQ_H [27 bytes ADS1299 frame] CHECKSUM 55
```

当前 `ble_sensor_gateway.py` 已实现：

- 按字节流缓存 BLE Notify，不假设一次 Notify 正好是一包。
- 搜索帧头 `AA` 并在错位时重同步。
- 校验包长度、帧类型、帧尾和 XOR checksum。
- 解析 `SEQ = SEQ_L + SEQ_H * 256`。
- 跳过 ADS1299 frame 中前 3 字节 status，从后续 8 个 24-bit 大端有符号补码通道解析 counts。
- 按协议换算原始电压：

```text
raw_uV = counts * 4.5 / 6 / 8388607 * 1_000_000
```

EEG 输出：

- 展示字段：`CH1_processed_uV` 到 `CH8_processed_uV`。
- 原始字段：`CH1_counts` 到 `CH8_counts`，以及 `CH1_raw_uV` 到 `CH8_raw_uV`。

`signal_processing.py` 中的 EEG 处理是轻量展示处理，主要包括去直流、线性去趋势、约 1 秒移动均值基线去除和 50Hz 陷波。它用于让页面波形更可读，不等同于完整临床 EEG 预处理流水线。后续如果要做严肃脑电特征，应在算法层明确滤波、伪迹处理、参考方式和通道质量控制。

## PPG/GSR 解析现状

硬件信息：

- BLE 设备名：`PPG_GSR`
- Service UUID：`6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- RX Characteristic：`6E400002-B5A3-F393-E0A9-E50E24DCCA9E`，上位机写命令。
- TX Characteristic：`6E400003-B5A3-F393-E0A9-E50E24DCCA9E`，硬件 Notify 回传。
- 开始连续采集命令：`AA 30 55`
- 停止连续采集命令：`AA 31 55`
- PPG 采样率：100Hz
- GSR 采样率：10Hz
- Notify 频率：10 包/s

连续采集批量帧为固定 71 字节：

```text
AA D0 BLOCK_H BLOCK_L FIRST_SEQ_H FIRST_SEQ_L STATUS
[10 groups: RED 3 bytes + IR 3 bytes]
GSR_H GSR_L CHECK 55
```

当前 `ble_sensor_gateway.py` 已实现：

- 按字节流缓存 BLE Notify，并对 71 字节 D0 帧重同步。
- 校验帧头、帧类型、帧尾和 XOR checksum。
- 解析 `BLOCK`、`FIRST_SEQ` 和 `STATUS`。
- 解析 10 个 PPG 样本，RED/IR 均按 18-bit 无符号值处理。
- 解析 1 个 GSR 样本，按 int16 大端补码处理。
- `STATUS bit0 = 1` 时将本包 GSR 标为无效。
- `STATUS bit1 = 1` 时将本包 PPG 标为无效。

PPG 输出：

- 展示字段：`HR_bpm`、`SpO2_pct`、`SpO2_RatioR`。
- 原始字段：`RED_raw`、`IR_raw`。

心率和血氧当前是基于 RED/IR 的滚动窗口估算：

- HR 使用 IR 波形去基线、平滑和峰值间隔估算。
- SpO2 使用 RED/IR 的 AC/DC ratio 估算。
- 这些值适合开发和趋势显示，不是医疗级校准结果。真实硬件验证时需要结合稳定佩戴、标定样本和异常处理再决定是否进入正式功能。

GSR 输出：

- 展示字段：`GSR_display_mV`、`GSR_display_V`、`GSR_physical_mV`、`GSR_physical_V`。
- 原始字段：`GSR_raw`。

协议中的物理换算是：

```text
GSR_V = gsr_raw * 2.048 / 32768
GSR_mV = GSR_V * 1000
```

示例 CSV 和当前页面沿用更直观的显示极性，因此 `GSR_display_* = -GSR_physical_*`。这只影响显示方向，不改变原始数据含义。

## Mock 网关现状

`mock_sensor_gateway.py` 使用 `hardware/EEG+GSR+PPG_test_data & matlab_code/` 中的 CSV 持续输出 WebSocket batch：

- EEG 读取 `EEG_raw_continuous_20260610_153657.csv`，以 500Hz 采样率输出，默认每批 125 点。
- PPG 读取 `PPG_100Hz_data.csv`，以 100Hz 采样率输出，默认每批 25 点。
- GSR 读取 `GSR_10Hz_data.csv`，以 10Hz 采样率输出，默认每批 2 或 3 点。

Mock 网关默认参数是低资源模式：

```bash
sensor-gateway/.venv/bin/python sensor-gateway/mock_sensor_gateway.py --batch-ms 250
```

如果后续算法需要原始 counts、RED/IR 或 GSR_raw，可显式打开：

```bash
sensor-gateway/.venv/bin/python sensor-gateway/mock_sensor_gateway.py --batch-ms 250 --include-raw
```

它的目的不是让前端直接读取 CSV，而是在没有硬件时模拟“已有硬件持续产生信号”。这样前端、业务逻辑和后续算法都提前面对真实上线时的 WebSocket 数据形态。

## 前端展示边界

干预页面只展示 `channelNames/samples` 中适合用户理解的字段，不展示 counts、raw、ADC 等硬件调试字段。

这样设计有三个原因：

- 用户界面更干净，不把硬件底层码值暴露给普通使用场景。
- 原始字段仍在网关代码中保留，后续算法和诊断可以通过 `--include-raw` 使用。
- 替换真实硬件时，前端展示逻辑不需要跟着硬件包格式变化。

如果后续需要检查丢包、原始 RED/IR、ADS1299 counts 或 GSR_raw，建议做单独的开发诊断页或后端日志，不放在正式干预页面。

## 接入真实硬件步骤

1. 确认服务器或采集主机可以访问 BLE 设备，并安装依赖：

```bash
cd /root/jry/chuxin
python3 -m venv sensor-gateway/.venv
sensor-gateway/.venv/bin/pip install -r sensor-gateway/requirements.txt
```

2. 本地先手动运行 BLE 网关。可以让程序按设备名扫描，也可以显式传 BLE 地址：

```bash
sensor-gateway/.venv/bin/python sensor-gateway/ble_sensor_gateway.py \
  --host 127.0.0.1 \
  --port 18081 \
  --path /chuxin-vue/sensor-gateway/ws
```

或：

```bash
sensor-gateway/.venv/bin/python sensor-gateway/ble_sensor_gateway.py \
  --eeg-address <EEG_BLE_ADDRESS> \
  --ppg-address <PPG_GSR_BLE_ADDRESS> \
  --host 127.0.0.1 \
  --port 18081 \
  --path /chuxin-vue/sensor-gateway/ws
```

3. 验证 WebSocket 输出：

```bash
wscat -c ws://127.0.0.1:18081/chuxin-vue/sensor-gateway/ws
```

至少确认：

- EEG 持续输出 500Hz，batch 内 50 个样本。
- PPG 持续输出 100Hz，batch 内 10 个样本。
- GSR 持续输出 10Hz，batch 内 1 个样本。
- `firstSeq` 或 `BLOCK/FIRST_SEQ` 连续递增。
- `status` 没有长期异常。
- 页面能看到稳定实时波形，浏览器没有明显卡顿。

4. 修改 systemd 的 `ExecStart`，从 mock 网关切换到 BLE 网关：

```ini
ExecStart=/root/jry/chuxin/sensor-gateway/.venv/bin/python /root/jry/chuxin/sensor-gateway/ble_sensor_gateway.py --host 127.0.0.1 --port 18081 --path /chuxin-vue/sensor-gateway/ws
```

如果设备地址固定，建议加入 `--eeg-address` 和 `--ppg-address`，避免扫描到同名设备或扫描耗时。

5. 重启服务并观察日志：

```bash
systemctl daemon-reload
systemctl restart chuxin-sensor-gateway
systemctl status chuxin-sensor-gateway
journalctl -u chuxin-sensor-gateway -n 100
```

低资源建议：

- 骨架阶段优先使用默认模式，不加 `--include-raw`。
- Mock 网关保持 `--batch-ms 250` 或更大；只有需要更细粒度 UI 动画时才降低。
- 前端干预页只保留短窗口和降采样波形，用于确认实时性，不作为原始数据记录器。

前端连接地址保持不变：

```text
wss://jp.jerrypsy.top/chuxin-vue/sensor-gateway/ws
```

## 验证清单

接真实硬件前后都建议检查：

- BLE 设备名或地址是否正确。
- EEG 是否收到 `AA 83 ... 55` 数据包，checksum 是否通过。
- PPG/GSR 是否收到 `AA D0 ... 55` 数据包，checksum 是否通过。
- EEG `SEQ` 是否连续。
- PPG/GSR `BLOCK` 是否每 100ms 增 1，`FIRST_SEQ` 是否每包增 10。
- `STATUS bit0` 和 `bit1` 是否经常报错。
- PPG 前几秒 HR/SpO2 可能为 `NaN`，这是滚动窗口尚未积累足够数据，不一定是异常。
- GSR 物理极性可能为负，显示层取反是预期设计。
- 页面只展示展示字段，原始字段通过 WS 保留但不显示。

## 已知限制

- BLE 网关已按硬件文档和 MATLAB 逻辑移植，但仍需要拿真实设备做长时间连接、丢包、重连和状态位验证。
- 当前 EEG 处理偏向实时显示，不是完整科研/医疗预处理流程。
- HR/SpO2 是开发阶段估算值，没有医疗校准，不能直接作为医学结论。
- 当前 WebSocket 使用 JSON，便于调试和维护；如果后续通道更多、采样率更高或需要长期记录，再考虑二进制协议。
- 当前没有把连续原始数据写入数据库。若未来需要记录，应单独设计采样文件或时序存储，不要让前端页面承担持久化。

## 资源占用原则

- 网关以 100ms batch 推送，避免逐点推送造成浏览器和 Vue 响应式压力。
- 前端只保留最近窗口的 ring buffer，不无限增长。
- 页面只渲染展示字段，raw/count 字段不进入可视化组件。
- 硬件解析、算法、UI、持久化分层处理，不在 parser 中混入业务逻辑。
- 默认继续使用 JSON，优先保持可读、易调试；只有在明确性能瓶颈出现时再升级为二进制 WS。
