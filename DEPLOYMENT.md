# 部署备注

## 前端部署到 `/chuxin-vue/`

线上访问地址是 `https://jp.jerrypsy.top/chuxin-vue/`，前端必须按子路径构建，否则 `index.html` 会引用 `/assets/...`，浏览器会到站点根目录加载资源并出现 503。

正确构建命令：

```bash
cd /root/jry/chuxin/frontend
VITE_APP_BASE=/chuxin-vue/ npm run build
```

正确部署命令：

```bash
rsync -a --delete /root/jry/chuxin/frontend/dist/ /var/www/html/chuxin-vue/
```

部署后检查：

```bash
curl -k -fsS https://jp.jerrypsy.top/chuxin-vue/ | rg '/chuxin-vue/assets/'
curl -k -fsS https://jp.jerrypsy.top/chuxin-vue/api/health
```

## 后端服务

后端监听 `18080`，Apache 将 `/chuxin-vue/api/` 代理到后端 `/api/`。

生产环境使用 systemd 托管后端服务，service 模板位于：

```bash
/root/jry/chuxin/deploy/systemd/chuxin-backend.service
```

首次安装或更新 service：

```bash
cp /root/jry/chuxin/deploy/systemd/chuxin-backend.service /etc/systemd/system/chuxin-backend.service
systemctl daemon-reload
systemctl enable --now chuxin-backend
```

发布新后端 jar 后重启：

```bash
cd /root/jry/chuxin/backend
./mvnw -q -DskipTests package  # 如无 mvnw，使用 mvn -q -DskipTests package
systemctl restart chuxin-backend
```

查看服务状态和日志：

```bash
systemctl status chuxin-backend
journalctl -u chuxin-backend -n 200
journalctl -u chuxin-backend -f
```

健康检查：

```bash
ss -ltnp | rg ':18080\b'
curl -fsS http://127.0.0.1:18080/api/health
curl -k -fsS https://jp.jerrypsy.top/chuxin-vue/api/health
```

不要再用 `backend/backend.log` 作为生产运行日志；服务日志统一通过 `journalctl -u chuxin-backend` 查看。

## 传感器 WebSocket 网关

前端实时信号页连接：

```bash
wss://jp.jerrypsy.top/chuxin-vue/sensor-gateway/ws
```

当前生产运行的是 mock hardware 网关：它读取 `hardware/` 中的真实采集数据，并通过同一套 WebSocket 协议模拟硬件持续输出。后续接真实 BLE 时，替换 service 的 `ExecStart` 为 `ble_sensor_gateway.py`，前端地址不变。硬件解析现状和接入步骤见 `/root/jry/chuxin/HARDWARE_SENSOR_GATEWAY.md`。

首次安装：

```bash
cd /root/jry/chuxin
python3 -m venv sensor-gateway/.venv
sensor-gateway/.venv/bin/pip install -r sensor-gateway/requirements.txt
cp /root/jry/chuxin/deploy/systemd/chuxin-sensor-gateway.service /etc/systemd/system/chuxin-sensor-gateway.service
systemctl daemon-reload
systemctl enable --now chuxin-sensor-gateway
```

Apache 需要代理 WebSocket。将以下配置加到 SSL vhost 中，并放在 `/chuxin-vue/` 的 `Alias` 之前：

```apache
ProxyPass /chuxin-vue/sensor-gateway/ws ws://127.0.0.1:18081/chuxin-vue/sensor-gateway/ws retry=0 timeout=86400
ProxyPassReverse /chuxin-vue/sensor-gateway/ws ws://127.0.0.1:18081/chuxin-vue/sensor-gateway/ws
```

配置模板位于：

```bash
/root/jry/chuxin/deploy/apache/chuxin-sensor-gateway.conf
```

检查：

```bash
systemctl status chuxin-sensor-gateway
journalctl -u chuxin-sensor-gateway -n 100
ss -ltnp | rg ':18081\b'
```
