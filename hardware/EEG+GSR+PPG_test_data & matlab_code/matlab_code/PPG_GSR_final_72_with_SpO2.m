clear; clc;

%% ================= BLE 参数 =================
% 可以用设备地址，也可以用设备名
deviceAddress = "F044D3E8F86F";   % 你的 PPG_GSR 蓝牙地址
deviceName    = "PPG_GSR";        % 备用：如果地址连不上，可改用名称

serviceUUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
rxUUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";  % MATLAB 写入 STM32
txUUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";  % STM32 Notify 给 MATLAB

disp("正在连接 BLE 设备...");

try
    dev = ble(deviceAddress);
catch
    warning("使用设备地址连接失败，尝试使用设备名连接。");
    dev = ble(deviceName);
end

rxChar = characteristic(dev, serviceUUID, rxUUID);
txChar = characteristic(dev, serviceUUID, txUUID);

subscribe(txChar);
pause(1);

disp("BLE 已连接并订阅 Notify。");


%% ================= 采集参数 =================
ppgFs = 100;                 % PPG 实际采样率 100 Hz
gsrFs = 10;                  % GSR 实际采样率 10 Hz
ppgPerBlock = 10;            % 每个 BLE 包包含 10 个 PPG 点
blockLen = 71;               % 新批量帧长度：71 字节

targetSec = 60;              % 采集时长，单位 s
targetPPGSamples = targetSec * ppgFs;
targetGSRSamples = targetSec * gsrFs;

plotInterval = 0.10;         % 图像刷新间隔，单位 s
displayWindowSec = 15;       % 显示最近 15 秒数据

% PPG 实时处理参数
ppgBaseSec = 1.5;            % 去 DC 基线窗口
ppgSmoothSec = 0.12;         % PPG 平滑窗口

% GSR 实时平滑参数
gsrSmoothSec = 1.0;          % GSR 是慢信号，可用 0.8~2 s

% ADS1113 电压换算参数
ads1113_fsr_v = 2.048;       % STM32 中 ADS1113 配置为 PGA ±2.048 V
gsr_lsb_v = ads1113_fsr_v / 32768;
gsrPolarity = -1;             % GSR显示极性：若显示方向反了，改成 -1

% 心率估算参数
hrWindowSec = 10;
hrUpdateInterval = 1.0;
minHR = 45;
maxHR = 180;

% SpO2 估算参数
% 说明：这里使用 RED/IR 的 AC/DC 比值做非医疗用途估算。
% spo2 = spo2A - spo2B * R 需要后续用标准血氧仪进行校准。
spo2WindowSec = 10;
spo2UpdateInterval = 1.0;
spo2A = 104;
spo2B = 17;


%% ================= 数据缓存 =================
seq_data = nan(targetPPGSamples, 1);
red_data = nan(targetPPGSamples, 1);
ir_data  = nan(targetPPGSamples, 1);
time_s   = nan(targetPPGSamples, 1);
hr_data  = nan(targetPPGSamples, 1);
spo2_data = nan(targetPPGSamples, 1);
spo2_ratio_data = nan(targetPPGSamples, 1);

gsr_time_s = nan(targetGSRSamples, 1);
gsr_block  = nan(targetGSRSamples, 1);
gsr_data   = nan(targetGSRSamples, 1);

validCount = 0;              % PPG 点计数
gsrCount = 0;                % GSR 点计数
rxBuffer = uint8([]);

lastPlotTime = 0;
lastHRTime = 0;
currentHR = NaN;

lastSpO2Time = 0;
currentSpO2 = NaN;
currentSpO2Ratio = NaN;

lastBlockSeq = NaN;
lostBlockCount = 0;


%% ================= 建立图窗 =================
fig = figure("Name", "Real-time PPG 100 Hz + GSR 10 Hz Block Receive");

tiledlayout(2, 1);

% ---------- PPG AC 波形 ----------
ax1 = nexttile;
hRed = plot(nan, nan, "LineWidth", 1.0);
hold on;
hIR = plot(nan, nan, "LineWidth", 1.4);
grid on;

xlabel("Time (s)");
ylabel("PPG AC component (ADC counts)");
title("Real-time PPG waveform, 100 Hz");
legend("RED AC", "IR AC", "Location", "best");

hrText = text(0.98, 0.88, "HR: -- bpm", ...
    "Units", "normalized", ...
    "HorizontalAlignment", "right", ...
    "FontSize", 16, ...
    "FontWeight", "bold", ...
    "Parent", ax1);

spo2Text = text(0.98, 0.74, "SpO2: -- %", ...
    "Units", "normalized", ...
    "HorizontalAlignment", "right", ...
    "FontSize", 16, ...
    "FontWeight", "bold", ...
    "Parent", ax1);

% ---------- GSR 波形 ----------
ax2 = nexttile;
hGSR = plot(nan, nan, "LineWidth", 1.4);
grid on;

xlabel("Time (s)");
ylabel("GSR voltage (mV)");
title("Real-time GSR signal, 10 Hz");


%% ================= 清除旧状态 =================
disp("发送停止采集命令 AA 31 55，清除旧状态。");
try
    write(rxChar, uint8([170 49 85]), "withresponse");     % AA 31 55
catch
    write(rxChar, uint8([170 49 85]), "withoutresponse");
end
pause(0.5);

% 尽量读掉可能残留的 ACK / 旧数据
for k = 1:5
    try
        tmp = read(txChar, "oldest"); %#ok<NASGU>
    catch
        break;
    end
end

rxBuffer = uint8([]);


%% ================= 开始连续采集 =================
disp("发送开始采集命令 AA 30 55。");
try
    write(rxChar, uint8([170 48 85]), "withresponse");     % AA 30 55
catch
    write(rxChar, uint8([170 48 85]), "withoutresponse");
end
pause(0.5);

disp("开始接收 D0 批量帧：每包 10 个 PPG 点 + 1 个 GSR 点。");


%% ================= 主循环 =================
tic;

try
    while validCount < targetPPGSamples && ishandle(fig)

        %% ---------- 读取 BLE Notify ----------
        try
            data = read(txChar, "oldest");
        catch
            pause(0.005);
            continue;
        end

        if isempty(data)
            pause(0.005);
            continue;
        end

        rxBuffer = [rxBuffer; uint8(data(:))];


        %% ---------- 从缓存中解析所有完整 71 字节 D0 帧 ----------
        while length(rxBuffer) >= blockLen

            idx = find(rxBuffer == hex2dec("AA"), 1, "first");

            if isempty(idx)
                rxBuffer = uint8([]);
                break;
            end

            if idx > 1
                rxBuffer = rxBuffer(idx:end);
            end

            if length(rxBuffer) < blockLen
                break;
            end

            frame = rxBuffer(1:blockLen);

            % 检查帧头、类型、帧尾
            if frame(1) ~= hex2dec("AA") || ...
               frame(2) ~= hex2dec("D0") || ...
               frame(blockLen) ~= hex2dec("55")

                % 可能是 ACK 帧 AA C1 55 / AA C2 55，或者残留数据
                rxBuffer = rxBuffer(2:end);
                continue;
            end

            % 校验：前 69 字节异或，第 70 字节为 CHECK，第 71 字节为 55
            check = uint8(0);
            for ii = 1:(blockLen - 2)
                check = bitxor(check, uint8(frame(ii)));
            end

            if check ~= uint8(frame(blockLen - 1))
                fprintf("校验错误，丢弃 1 字节重新同步。\n");
                rxBuffer = rxBuffer(2:end);
                continue;
            end

            % 移除已解析帧
            rxBuffer = rxBuffer(blockLen+1:end);


            %% ---------- 解析 D0 批量帧 ----------
            blockSeq = double(frame(3)) * 256 + double(frame(4));
            firstSeq = double(frame(5)) * 256 + double(frame(6));
            statusByte = frame(7);

            % 检测丢包
            if ~isnan(lastBlockSeq)
                blockDiff = mod(blockSeq - lastBlockSeq, 65536);
                if blockDiff ~= 1
                    lostBlockCount = lostBlockCount + double(blockDiff - 1);
                    fprintf("可能丢包：上一BLOCK=%d，当前BLOCK=%d，间隔=%d\n", ...
                        lastBlockSeq, blockSeq, blockDiff);
                end
            end
            lastBlockSeq = blockSeq;

            if bitand(statusByte, hex2dec("01"))
                fprintf("BLOCK=%d：GSR读取失败\n", blockSeq);
            end

            if bitand(statusByte, hex2dec("02"))
                fprintf("BLOCK=%d：PPG读取失败\n", blockSeq);
            end

            pos = 8;

            %% ---------- 解析 10 个 PPG 点 ----------
            for kk = 1:ppgPerBlock

                if validCount >= targetPPGSamples
                    break;
                end

                validCount = validCount + 1;

                red = double(frame(pos)) * 65536 + ...
                      double(frame(pos+1)) * 256 + ...
                      double(frame(pos+2));

                ir  = double(frame(pos+3)) * 65536 + ...
                      double(frame(pos+4)) * 256 + ...
                      double(frame(pos+5));

                pos = pos + 6;

                thisSeq = firstSeq + kk - 1;

                seq_data(validCount) = thisSeq;
                red_data(validCount) = red;
                ir_data(validCount)  = ir;

                % 用样本序号重建时间轴，避免 MATLAB 接收抖动影响时间
                time_s(validCount) = (thisSeq - 1) / ppgFs;

                hr_data(validCount) = currentHR;
                spo2_data(validCount) = currentSpO2;
                spo2_ratio_data(validCount) = currentSpO2Ratio;
            end


            %% ---------- 解析 1 个 GSR 点 ----------
            gsr = double(frame(pos)) * 256 + double(frame(pos+1));

            if gsr >= 32768
                gsr = gsr - 65536;
            end

            gsrCount = gsrCount + 1;

            if gsrCount <= targetGSRSamples
                gsr_block(gsrCount) = blockSeq;
                gsr_data(gsrCount) = gsr;

                % GSR 10 Hz 时间轴
                gsr_time_s(gsrCount) = (blockSeq - 1) / gsrFs;
            end


            %% ---------- 心率估算 ----------
            if validCount > 30 && time_s(validCount) - lastHRTime >= hrUpdateInterval
                lastHRTime = time_s(validCount);

                [hrEstimate, ~] = estimateHeartRateFromIR( ...
                    time_s(1:validCount), ...
                    ir_data(1:validCount), ...
                    hrWindowSec, ...
                    minHR, ...
                    maxHR);

                if ~isnan(hrEstimate)
                    currentHR = hrEstimate;
                    hr_data(validCount) = currentHR;
                    set(hrText, "String", sprintf("HR: %.0f bpm", currentHR));
                else
                    set(hrText, "String", "HR: -- bpm");
                end
            end


            %% ---------- SpO2 估算 ----------
            if validCount > 5 * ppgFs && time_s(validCount) - lastSpO2Time >= spo2UpdateInterval
                lastSpO2Time = time_s(validCount);

                [spo2Estimate, ratioR] = estimateSpO2FromRedIR( ...
                    time_s(1:validCount), ...
                    red_data(1:validCount), ...
                    ir_data(1:validCount), ...
                    spo2WindowSec, ...
                    spo2A, ...
                    spo2B);

                if ~isnan(spo2Estimate)
                    currentSpO2 = spo2Estimate;
                    currentSpO2Ratio = ratioR;
                    spo2_data(validCount) = currentSpO2;
                    spo2_ratio_data(validCount) = currentSpO2Ratio;
                    set(spo2Text, "String", sprintf("SpO2: %.0f %%", currentSpO2));
                else
                    currentSpO2 = NaN;
                    currentSpO2Ratio = NaN;
                    set(spo2Text, "String", "SpO2: -- %");
                end
            end


            %% ---------- 实时绘图 ----------
            if validCount > 10 && time_s(validCount) - lastPlotTime >= plotInterval
                lastPlotTime = time_s(validCount);

                tAll = time_s(1:validCount);
                redAll = double(red_data(1:validCount));
                irAll  = double(ir_data(1:validCount));

                tNow = tAll(end);

                idxWin = tAll >= max(0, tNow - displayWindowSec);

                tPlot = tAll(idxWin);
                redPlot = redAll(idxWin);
                irPlot  = irAll(idxWin);

                if numel(tPlot) > 5

                    fsPlot = ppgFs;

                    % ---------- PPG 去 DC + 平滑 ----------
                    baseWin = max(5, round(fsPlot * ppgBaseSec));
                    smoothWin = max(3, round(fsPlot * ppgSmoothSec));

                    redAC = redPlot - movmean(redPlot, baseWin, "omitnan");
                    irAC  = irPlot  - movmean(irPlot,  baseWin, "omitnan");

                    redAC = movmean(redAC, smoothWin, "omitnan");
                    irAC  = movmean(irAC,  smoothWin, "omitnan");

                    % 如果你的 PPG 显示方向已经对了，可把下面两句注释掉
                    redAC = -redAC;
                    irAC  = -irAC;

                    set(hRed, "XData", tPlot, "YData", redAC);
                    set(hIR,  "XData", tPlot, "YData", irAC);

                    xlim(ax1, [max(0, tNow - displayWindowSec), max(displayWindowSec, tNow)]);

                    ymin = min([redAC(:); irAC(:)]);
                    ymax = max([redAC(:); irAC(:)]);

                    if ymin ~= ymax
                        margin = 0.20 * abs(ymax - ymin);
                        ylim(ax1, [ymin - margin, ymax + margin]);
                    end
                end


                %% ---------- GSR 绘图，10 Hz ----------
                if gsrCount > 3
                    validGSRNow = 1:min(gsrCount, targetGSRSamples);

                    tGSRAll = gsr_time_s(validGSRNow);
                    gsrAll_mV = gsrPolarity * double(gsr_data(validGSRNow)) * gsr_lsb_v * 1000;

                    idxGSRWin = tGSRAll >= max(0, tNow - displayWindowSec);

                    tGSRPlot = tGSRAll(idxGSRWin);
                    gsrPlot = gsrAll_mV(idxGSRWin);

                    if numel(gsrPlot) > 3
                        gsrWin = max(3, round(gsrFs * gsrSmoothSec));
                        gsrSmooth = movmean(gsrPlot, gsrWin, "omitnan");

                        set(hGSR, "XData", tGSRPlot, "YData", gsrSmooth);

                        xlim(ax2, [max(0, tNow - displayWindowSec), max(displayWindowSec, tNow)]);

                        gmin = min(gsrSmooth);
                        gmax = max(gsrSmooth);

                        if gmin ~= gmax
                            margin = 0.15 * abs(gmax - gmin);
                            ylim(ax2, [gmin - margin, gmax + margin]);
                        end
                    end
                end

                drawnow limitrate;
            end


            %% ---------- 状态打印 ----------
            if mod(validCount, 100) == 0
                fprintf("已解析 PPG=%d 点，GSR=%d 点，BLOCK=%d，FIRST_SEQ=%d，GSR=%d，HR=%.1f bpm，SpO2=%.1f %%\n", ...
                    validCount, gsrCount, blockSeq, firstSeq, gsr, currentHR, currentSpO2);
            end

            if validCount >= targetPPGSamples
                break;
            end
        end
    end

catch ME
    disp("采集中断：");
    disp(ME.message);
end


%% ================= 停止连续采集 =================
disp("发送停止采集命令 AA 31 55。");

try
    write(rxChar, uint8([170 49 85]), "withresponse");
catch
    write(rxChar, uint8([170 49 85]), "withoutresponse");
end

pause(0.5);


%% ================= 计算实际接收情况 =================
validPPG = ~isnan(time_s);
validGSR = ~isnan(gsr_time_s);

fprintf("\n========== 采集统计 ==========\n");

if sum(validPPG) > 2
    t1 = time_s(find(validPPG, 1, "first"));
    t2 = time_s(find(validPPG, 1, "last"));
    fs_ppg_actual = (sum(validPPG) - 1) / max(t2 - t1, eps);

    fprintf("PPG 有效点数 = %d\n", sum(validPPG));
    fprintf("PPG 重建采样率约 = %.2f Hz\n", fs_ppg_actual);
else
    disp("PPG 有效数据太少，无法计算采样率。");
end

if sum(validGSR) > 2
    t1 = gsr_time_s(find(validGSR, 1, "first"));
    t2 = gsr_time_s(find(validGSR, 1, "last"));
    fs_gsr_actual = (sum(validGSR) - 1) / max(t2 - t1, eps);

    fprintf("GSR 有效点数 = %d\n", sum(validGSR));
    fprintf("GSR 重建采样率约 = %.2f Hz\n", fs_gsr_actual);
else
    disp("GSR 有效数据太少，无法计算采样率。");
end

fprintf("检测到可能丢失 BLOCK 数 = %d\n", lostBlockCount);


%% ================= 保存数据 =================
validPPG = ~isnan(time_s);
validGSR = ~isnan(gsr_time_s);

gsr_voltage_v = gsrPolarity * gsr_data * gsr_lsb_v;
gsr_voltage_mV = gsr_voltage_v * 1000;

ppgTable = table( ...
    time_s(validPPG), ...
    seq_data(validPPG), ...
    red_data(validPPG), ...
    ir_data(validPPG), ...
    hr_data(validPPG), ...
    spo2_data(validPPG), ...
    spo2_ratio_data(validPPG), ...
    'VariableNames', {'Time_s', 'SEQ', 'RED_raw', 'IR_raw', 'HR_bpm', 'SpO2_pct', 'SpO2_RatioR'} ...
);

gsrTable = table( ...
    gsr_time_s(validGSR), ...
    gsr_block(validGSR), ...
    gsr_data(validGSR), ...
    gsr_voltage_v(validGSR), ...
    gsr_voltage_mV(validGSR), ...
    'VariableNames', {'Time_s', 'BLOCK', 'GSR_raw', 'GSR_V', 'GSR_mV'} ...
);

save("PPG_GSR_block_data.mat", ...
    "time_s", "seq_data", "red_data", "ir_data", "hr_data", ...
    "spo2_data", "spo2_ratio_data", ...
    "gsr_time_s", "gsr_block", "gsr_data", ...
    "gsr_voltage_v", "gsr_voltage_mV", ...
    "lostBlockCount");

writetable(ppgTable, "PPG_100Hz_data.csv");
writetable(gsrTable, "GSR_10Hz_data.csv");

disp("数据已保存：");
disp("PPG_100Hz_data.csv");
disp("GSR_10Hz_data.csv");
disp("PPG_GSR_block_data.mat");


%% ================= 局部函数：根据 RED/IR PPG 估算 SpO2 =================
function [spo2_pct, ratioR] = estimateSpO2FromRedIR(t, redRaw, irRaw, windowSec, spo2A, spo2B)

    spo2_pct = NaN;
    ratioR = NaN;

    t = t(:);
    redRaw = double(redRaw(:));
    irRaw  = double(irRaw(:));

    valid = ~isnan(t) & ~isnan(redRaw) & ~isnan(irRaw);
    t = t(valid);
    redRaw = redRaw(valid);
    irRaw  = irRaw(valid);

    if numel(t) < 100
        return;
    end

    tEnd = t(end);
    idx = t >= (tEnd - windowSec);

    tw = t(idx);
    red = redRaw(idx);
    ir  = irRaw(idx);

    if numel(tw) < 100 || (tw(end) - tw(1)) < 5
        return;
    end

    fs = (numel(tw) - 1) / max(tw(end) - tw(1), eps);
    if fs < 5
        return;
    end

    % DC：窗口内平均值
    redDC = mean(red, "omitnan");
    irDC  = mean(ir,  "omitnan");

    if redDC <= 1000 || irDC <= 1000
        return;
    end

    % AC：先去掉慢变化基线，再用 RMS 表示脉动幅度
    baseWin = max(5, round(fs * 1.5));
    redACSignal = red - movmean(red, baseWin, "omitnan");
    irACSignal  = ir  - movmean(ir,  baseWin, "omitnan");

    redAC = sqrt(mean(redACSignal.^2, "omitnan"));
    irAC  = sqrt(mean(irACSignal.^2,  "omitnan"));

    if redAC <= 1 || irAC <= 1
        return;
    end

    ratioR = (redAC / redDC) / (irAC / irDC);

    % 简单质量控制：R 太离谱时不显示 SpO2
    if ratioR < 0.2 || ratioR > 2.0
        spo2_pct = NaN;
        return;
    end

    % 经验线性公式，未校准。后续建议用标准血氧仪重新拟合 spo2A/spo2B
    spo2Raw = spo2A - spo2B * ratioR;

    % 合理范围控制。100~105 之间按 100 显示，其他异常值不输出。
    if spo2Raw >= 70 && spo2Raw <= 105
        spo2_pct = min(100, max(70, spo2Raw));
    else
        spo2_pct = NaN;
    end
end


%% ================= 局部函数：根据 IR PPG 估算心率 =================
function [hr_bpm, peakTimes] = estimateHeartRateFromIR(t, irRaw, windowSec, minHR, maxHR)

    hr_bpm = NaN;
    peakTimes = [];

    t = t(:);
    irRaw = double(irRaw(:));

    valid = ~isnan(t) & ~isnan(irRaw);
    t = t(valid);
    irRaw = irRaw(valid);

    if numel(t) < 30
        return;
    end

    tEnd = t(end);
    idx = t >= (tEnd - windowSec);

    tw = t(idx);
    xw = irRaw(idx);

    if numel(tw) < 30 || (tw(end) - tw(1)) < 5
        return;
    end

    fs = (numel(tw) - 1) / max(tw(end) - tw(1), eps);

    if fs < 5
        return;
    end

    % 去 DC + 平滑
    baseWin = max(5, round(fs * 1.5));
    smoothWin = max(3, round(fs * 0.12));

    x = xw - movmean(xw, baseWin, "omitnan");
    x = movmean(x, smoothWin, "omitnan");

    % 有些 PPG 峰朝上，有些朝下，正反都试
    [hr1, p1, score1] = findPPGPeaks(tw, x, minHR, maxHR);
    [hr2, p2, score2] = findPPGPeaks(tw, -x, minHR, maxHR);

    if score1 >= score2
        hr_bpm = hr1;
        peakTimes = p1;
    else
        hr_bpm = hr2;
        peakTimes = p2;
    end
end


%% ================= 局部函数：找 PPG 峰并计算 HR =================
function [hr_bpm, peakTimes, score] = findPPGPeaks(t, x, minHR, maxHR)

    hr_bpm = NaN;
    peakTimes = [];
    score = 0;

    t = t(:);
    x = x(:);

    if numel(x) < 10 || std(x) < eps
        return;
    end

    minInterval = 60 / maxHR;
    maxInterval = 60 / minHR;

    threshold = median(x) + 0.35 * std(x);

    cand = find( ...
        x(2:end-1) > x(1:end-2) & ...
        x(2:end-1) >= x(3:end) & ...
        x(2:end-1) > threshold) + 1;

    if isempty(cand)
        return;
    end

    selected = [];

    for k = 1:numel(cand)
        c = cand(k);

        if isempty(selected)
            selected = c;
        else
            last = selected(end);

            if (t(c) - t(last)) >= minInterval
                selected(end+1) = c; %#ok<AGROW>
            else
                if x(c) > x(last)
                    selected(end) = c;
                end
            end
        end
    end

    if numel(selected) < 3
        return;
    end

    peakTimes = t(selected);
    intervals = diff(peakTimes);

    good = intervals >= minInterval & intervals <= maxInterval;
    intervals = intervals(good);

    if numel(intervals) < 2
        return;
    end

    hr_bpm = 60 / median(intervals);

    if hr_bpm < minHR || hr_bpm > maxHR
        hr_bpm = NaN;
        peakTimes = [];
        score = 0;
        return;
    end

    score = numel(intervals) * std(x(selected));
end