%% EEG_CONTINUOUS_SaveWhileRecording.m
% 功能：
% 1. 连接 EEG_8CH
% 2. 发送 START: AA 31 55
% 3. 持续接收 EEG 二进制包：AA 83 SEQ_L SEQ_H [27 bytes] CHECKSUM 55
% 4. 转换为 uV
% 5. 一个 Figure 内显示 8 个通道 processed EEG
% 6. 横坐标为真实采集时间，并随采集滚动
% 7. 边采集边保存：
%    - raw CSV：原始 counts + raw uV，每个有效包都保存
%    - processed CSV：figure 展示用的预处理数据，按刷新点保存
% 8. 不按固定时间自动停止
% 9. 关闭 Figure 或 Ctrl+C 才停止；停止时发送 STOP 并关闭文件

clear; clc;

%% ===================== ADS1299 参数 =====================
FS = 500;          % CONFIG1=0x95，对应 500 Hz
VREF = 4.5;        % ADS1299 内部参考电压，单位 V
GAIN = 6;         % CHnSET=0x60，对应 gain=24

LSB_uV = VREF / GAIN / (2^23 - 1) * 1e6;

fprintf("ADS1299 换算系数：1 count = %.6f uV\n", LSB_uV);
fprintf("采样率 FS = %d Hz\n", FS);

%% ===================== 采集与显示参数 =====================
DISPLAY_SECONDS = 5;                 % 图上显示最近多少秒
maxDisplayPoints = FS * DISPLAY_SECONDS;

PLOT_UPDATE_EVERY = 2;               % 1最快，但500Hz时可能卡；推荐2或5
PRINT_EVERY = 500;                   % 每多少个有效包打印一次状态
FLUSH_EVERY = 500;                   % 每多少个有效包强制刷新保存到磁盘

AUTO_YLIM = true;                    % true = 纵坐标随信号自动变化
MIN_Y_RANGE = 100;                   % 最小纵坐标范围，单位 uV
Y_MARGIN = 0.25;                     % 上下留白比例
Y_SMOOTH = 0.85;                     % 纵坐标平滑系数
yLimCurrent = repmat([-100 100], 8, 1);

%% ===================== BLE 参数 =====================
DEVICE_NAME = "EEG_8CH";
DEVICE_ADDR = "F044D3EC9581";

SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E";
TX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E";   % MATLAB -> STM32
RX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E";   % STM32 -> MATLAB

START_CMD = uint8([hex2dec('AA'), hex2dec('31'), hex2dec('55')]);
STOP_CMD  = uint8([hex2dec('AA'), hex2dec('32'), hex2dec('55')]);

%% ===================== 保存文件准备 =====================
timestamp = datestr(now, "yyyymmdd_HHMMSS");
saveDir = fullfile(pwd, "EEG_saved_data");

if ~exist(saveDir, "dir")
    mkdir(saveDir);
end

rawCsvFile = fullfile(saveDir, sprintf("EEG_raw_continuous_%s.csv", timestamp));
processedCsvFile = fullfile(saveDir, sprintf("EEG_processed_continuous_%s.csv", timestamp));
matFile = fullfile(saveDir, sprintf("EEG_metadata_continuous_%s.mat", timestamp));

rawFID = fopen(rawCsvFile, "w");
if rawFID < 0
    error("无法创建 raw CSV 文件");
end

processedFID = fopen(processedCsvFile, "w");
if processedFID < 0
    fclose(rawFID);
    error("无法创建 processed CSV 文件");
end

%% 写 raw CSV 表头
fprintf(rawFID, "Time_s,Seq,");
for ch = 1:8
    fprintf(rawFID, "CH%d_counts,", ch);
end
for ch = 1:8
    if ch < 8
        fprintf(rawFID, "CH%d_raw_uV,", ch);
    else
        fprintf(rawFID, "CH%d_raw_uV\n", ch);
    end
end

%% 写 processed CSV 表头
fprintf(processedFID, "Time_s,Seq,");
for ch = 1:8
    if ch < 8
        fprintf(processedFID, "CH%d_processed_uV,", ch);
    else
        fprintf(processedFID, "CH%d_processed_uV\n", ch);
    end
end

disp("数据将实时保存到：");
disp(rawCsvFile);
disp(processedCsvFile);

%% ===================== 运行状态变量 =====================
rxBuffer = uint8([]);

timeWin = nan(maxDisplayPoints, 1);
seqWin = nan(maxDisplayPoints, 1);
rawWin_uV = nan(maxDisplayPoints, 8);

lastSeq = [];
firstSeq = [];
lostPackets = 0;
validPackets = 0;
badPackets = 0;
totalBytesReceived = 0;

latestProcessedWindow = [];
latestProcessedTime = [];

%% ===================== 扫描并连接 BLE =====================
disp("正在扫描 BLE 设备...");
devices = blelist("Timeout", 10);
disp(devices);

idx = strcmp(string(devices.Name), DEVICE_NAME) | ...
      strcmp(string(devices.Address), DEVICE_ADDR);

if ~any(idx)
    fclose(rawFID);
    fclose(processedFID);
    error("没有扫描到 EEG_8CH，请确认蓝牙模块已上电，并且没有被其他设备连接。");
end

disp("正在连接 EEG_8CH...");
b = ble(DEVICE_ADDR);

rxChar = characteristic(b, SERVICE_UUID, RX_CHAR_UUID);
txChar = characteristic(b, SERVICE_UUID, TX_CHAR_UUID);

subscribe(rxChar);

disp("BLE 已连接。");

%% 异常退出时也尽量发送 STOP 和关闭文件
cleanupObj = onCleanup(@()cleanupContinuousEEG(txChar, STOP_CMD, rawFID, processedFID));

%% ===================== 发送 START =====================
write(txChar, START_CMD, "withoutresponse");
disp("已发送 START: AA 31 55");
pause(0.5);

%% ===================== 一个 Figure 内显示 8 个通道 =====================
fig1 = figure("Name", "ADS1299 EEG 8CH Continuous");
tl = tiledlayout(fig1, 8, 1, "TileSpacing", "compact", "Padding", "compact");

axAll = gobjects(1, 8);
hAll = gobjects(1, 8);

for ch = 1:8
    axAll(ch) = nexttile(tl);
    hAll(ch) = plot(axAll(ch), nan, nan, "LineWidth", 0.8);
    grid(axAll(ch), "on");

    title(axAll(ch), sprintf("CH%d", ch));
    ylabel(axAll(ch), "Voltage (\muV)");
    xlabel(axAll(ch), "Time (s)");

    ylim(axAll(ch), yLimCurrent(ch, :));
    xlim(axAll(ch), [0 DISPLAY_SECONDS]);
end

sgtitle(tl, "ADS1299 8-channel processed signal - continuous recording");

%% ===================== STOP 按钮：停止采集但不断蓝牙 =====================
setappdata(fig1, "stopRequested", false);

uicontrol(fig1, ...
    "Style", "pushbutton", ...
    "String", "STOP采集", ...
    "Units", "normalized", ...
    "Position", [0.86 0.955 0.13 0.035], ...
    "FontSize", 10, ...
    "Callback", @(src, event)setappdata(fig1, "stopRequested", true));

%% ===================== 持续接收循环 =====================
disp("开始持续接收 EEG 数据...");
disp("关闭 Figure 或 Ctrl+C 才会停止。");
disp("--------------------------------------------------");

tStart = tic;
running = true;

while running

    if ~isvalid(fig1)
        disp("图窗已关闭，准备停止采集。");
        break;
    end

    if getappdata(fig1, "stopRequested")
        disp("已点击 STOP，准备停止硬件采集，但保持 BLE 连接。");
        break;
    end

    %% 读取 BLE 数据
    try
        data = read(rxChar, "oldest");

    catch ME
        msg = string(ME.message);

        if contains(msg, "No new data", "IgnoreCase", true) || ...
           contains(msg, "尚未", "IgnoreCase", true) || ...
           contains(msg, "new data", "IgnoreCase", true)
            pause(0.0005);
            continue;
        else
            disp("接收过程出现错误，准备停止采集。");
            disp(msg);
            break;
        end
    end

    if isempty(data)
        pause(0.0005);
        continue;
    end

    data = uint8(data);
    totalBytesReceived = totalBytesReceived + numel(data);
    rxBuffer = [rxBuffer, data(:).'];

    %% ===================== 解包 =====================
    while numel(rxBuffer) >= 3

        %% 找 AA 帧头
        idxHead = find(rxBuffer == hex2dec('AA'), 1);

        if isempty(idxHead)
            rxBuffer = uint8([]);
            break;
        end

        if idxHead > 1
            rxBuffer = rxBuffer(idxHead:end);
        end

        if numel(rxBuffer) < 3
            break;
        end

        %% 解析 ACK_START: AA B1 55
        if rxBuffer(2) == hex2dec('B1')
            if numel(rxBuffer) >= 3 && rxBuffer(3) == hex2dec('55')
                disp("收到下位机 ACK_START: AA B1 55");
                rxBuffer = rxBuffer(4:end);
                continue;
            else
                rxBuffer = rxBuffer(2:end);
                continue;
            end
        end

        %% 解析 ACK_STOP: AA B2 55
        if rxBuffer(2) == hex2dec('B2')
            if numel(rxBuffer) >= 3 && rxBuffer(3) == hex2dec('55')
                disp("收到下位机 ACK_STOP: AA B2 55");
                rxBuffer = rxBuffer(4:end);
                continue;
            else
                rxBuffer = rxBuffer(2:end);
                continue;
            end
        end

        %% EEG 数据包必须是 AA 83，总长度 33
        if rxBuffer(2) ~= hex2dec('83')
            rxBuffer = rxBuffer(2:end);
            continue;
        end

        if numel(rxBuffer) < 33
            break;
        end

        pkt = rxBuffer(1:33);

        %% 帧尾检查
        if pkt(33) ~= hex2dec('55')
            rxBuffer = rxBuffer(2:end);
            badPackets = badPackets + 1;
            continue;
        end

        %% 校验检查
        checksum = uint8(0);
        for k = 1:31
            checksum = bitxor(checksum, pkt(k));
        end

        if checksum ~= pkt(32)
            rxBuffer = rxBuffer(2:end);
            badPackets = badPackets + 1;
            continue;
        end

        %% ===================== 有效 EEG 包 =====================
        validPackets = validPackets + 1;

        seq = double(pkt(3)) + double(pkt(4)) * 256;

        if isempty(firstSeq)
            firstSeq = seq;
        end

        if ~isempty(lastSeq)
            expectedSeq = mod(lastSeq + 1, 65536);
            if seq ~= expectedSeq
                lostPackets = lostPackets + mod(seq - expectedSeq, 65536);
            end
        end

        lastSeq = seq;

        %% 时间轴
        sampleIndex = validPackets;
        tSample = (sampleIndex - 1) / FS;

        %% ADS1299 原始帧
        adsFrame = pkt(5:31);  % 27 bytes: status 3 + 8ch * 3

        chCounts = zeros(1, 8);

        for ch = 1:8
            base = 4 + (ch - 1) * 3;

            b1 = double(adsFrame(base));
            b2 = double(adsFrame(base + 1));
            b3 = double(adsFrame(base + 2));

            value = b1 * 65536 + b2 * 256 + b3;

            if value >= 2^23
                value = value - 2^24;
            end

            chCounts(ch) = value;
        end

        ch_uV = chCounts * LSB_uV;

        %% ===================== 边采集边保存 raw 数据 =====================
        fprintf(rawFID, "%.6f,%d,", tSample, seq);

        for ch = 1:8
            fprintf(rawFID, "%d,", round(chCounts(ch)));
        end

        for ch = 1:8
            if ch < 8
                fprintf(rawFID, "%.6f,", ch_uV(ch));
            else
                fprintf(rawFID, "%.6f\n", ch_uV(ch));
            end
        end

        %% ===================== 更新显示窗口缓存 =====================
        if validPackets <= maxDisplayPoints
            idx = validPackets;
            timeWin(idx) = tSample;
            seqWin(idx) = seq;
            rawWin_uV(idx, :) = ch_uV;
        else
            timeWin(1:end-1) = timeWin(2:end);
            timeWin(end) = tSample;

            seqWin(1:end-1) = seqWin(2:end);
            seqWin(end) = seq;

            rawWin_uV(1:end-1, :) = rawWin_uV(2:end, :);
            rawWin_uV(end, :) = ch_uV;
        end

        %% ===================== 实时显示 + 边保存 processed =====================
        if mod(validPackets, PLOT_UPDATE_EVERY) == 0

            validRows = ~isnan(timeWin);
            tWin = timeWin(validRows);
            seqWinValid = seqWin(validRows);
            rawSegment_uV = rawWin_uV(validRows, :);

            procWin_uV = preprocessEEGDisplay(rawSegment_uV, FS);

            latestProcessedWindow = procWin_uV;
            latestProcessedTime = tWin;

            %% 取当前窗口最后一个点作为 processed 记录值，边采边保存
            latestProc = procWin_uV(end, :);
            latestSeq = seqWinValid(end);
            latestTime = tWin(end);

            fprintf(processedFID, "%.6f,%d,", latestTime, latestSeq);

            for ch = 1:8
                if ch < 8
                    fprintf(processedFID, "%.6f,", latestProc(ch));
                else
                    fprintf(processedFID, "%.6f\n", latestProc(ch));
                end
            end

            %% 更新 Figure
            for ch = 1:8
                yData = procWin_uV(:, ch);

                set(hAll(ch), "XData", tWin, "YData", yData);

                if AUTO_YLIM
                    v = yData(~isnan(yData));

                    if ~isempty(v)
                        yMin = min(v);
                        yMax = max(v);

                        yCenter = (yMax + yMin) / 2;
                        yRange = yMax - yMin;

                        if yRange < MIN_Y_RANGE
                            yRange = MIN_Y_RANGE;
                        end

                        yHalf = yRange * (1 + Y_MARGIN) / 2;
                        targetYLim = [yCenter - yHalf, yCenter + yHalf];

                        yLimCurrent(ch, :) = Y_SMOOTH * yLimCurrent(ch, :) + ...
                                             (1 - Y_SMOOTH) * targetYLim;

                        ylim(axAll(ch), yLimCurrent(ch, :));
                    end
                end
            end

            %% 横坐标跟随真实时间滚动
            tNow = tWin(end);

            if tNow <= DISPLAY_SECONDS
                for ch = 1:8
                    xlim(axAll(ch), [0 DISPLAY_SECONDS]);
                end
            else
                for ch = 1:8
                    xlim(axAll(ch), [tNow - DISPLAY_SECONDS, tNow]);
                end
            end

            drawnow limitrate nocallbacks;
        end

        %% ===================== 定期强制刷新文件到磁盘 =====================
        if mod(validPackets, FLUSH_EVERY) == 0
            fclose(rawFID);
            fclose(processedFID);

            rawFID = fopen(rawCsvFile, "a");
            processedFID = fopen(processedCsvFile, "a");
        end

        %% ===================== 打印状态 =====================
        if mod(validPackets, PRINT_EVERY) == 0
            elapsed = toc(tStart);
            actualFs = validPackets / elapsed;

            fprintf("有效包=%d, 坏包=%d, 丢包估计=%d, 最新SEQ=%d, 采集时间=%.2fs, 实际接收=%.2f Hz\n", ...
                validPackets, badPackets, lostPackets, seq, tSample, actualFs);

            if ~isempty(latestProcessedWindow)
                rms_each = zeros(1, 8);
                pp_each = zeros(1, 8);

                for ch = 1:8
                    v = latestProcessedWindow(:, ch);
                    v = v(~isnan(v));

                    if isempty(v)
                        rms_each(ch) = NaN;
                        pp_each(ch) = NaN;
                    else
                        rms_each(ch) = sqrt(mean(v.^2));
                        pp_each(ch) = max(v) - min(v);
                    end
                end

                [~, idxNoise] = maxk(rms_each, 2);

                fprintf("RMS uV: ");
                fprintf("CH%d=%.1f ", [1:8; rms_each]);
                fprintf("\n");

                fprintf("PP uV : ");
                fprintf("CH%d=%.1f ", [1:8; pp_each]);
                fprintf("\n");

                fprintf("当前噪声最大的两个通道：CH%d 和 CH%d\n", ...
                    idxNoise(1), idxNoise(2));
            end
        end

        %% 删除已解析包
        rxBuffer = rxBuffer(34:end);
    end

    pause(0.0005);
end

%% ===================== 手动停止后收尾 =====================
disp("准备发送 STOP: AA 32 55");
try
    write(txChar, STOP_CMD, "withoutresponse");
    disp("已发送 STOP: AA 32 55");
catch
    disp("STOP 发送失败。");
end

pause(0.3);

%% 保存 metadata
metadata = struct();
metadata.FS = FS;
metadata.VREF = VREF;
metadata.GAIN = GAIN;
metadata.LSB_uV = LSB_uV;
metadata.ValidPackets = validPackets;
metadata.BadPackets = badPackets;
metadata.LostPackets = lostPackets;
metadata.TotalBytesReceived = totalBytesReceived;
metadata.StartCommand = "AA 31 55";
metadata.StopCommand = "AA 32 55";
metadata.PacketFormat = "AA 83 SEQ_L SEQ_H 27bytes CHECKSUM 55";
metadata.DisplaySeconds = DISPLAY_SECONDS;
metadata.PlotUpdateEvery = PLOT_UPDATE_EVERY;
metadata.RawCsvFile = rawCsvFile;
metadata.ProcessedCsvFile = processedCsvFile;

save(matFile, "metadata", "latestProcessedTime", "latestProcessedWindow");

%% 关闭文件
try
    fclose(rawFID);
catch
end

try
    fclose(processedFID);
catch
end

%% 不 clear BLE 对象，不 unsubscribe，保持蓝牙连接
% 不要执行 clear b rxChar txChar
% 不要执行 unsubscribe(rxChar)
% cleanupObj 保留在工作区，异常时仍可尝试发送 STOP

disp("--------------------------------------------------");
fprintf("接收结束。\n");
fprintf("有效包：%d\n", validPackets);
fprintf("坏包：%d\n", badPackets);
fprintf("丢包估计：%d\n", lostPackets);
fprintf("metadata MAT：%s\n", matFile);
disp("数据已边采边保存。");
disp("如果需要手动断开蓝牙，在命令行执行：clear b rxChar txChar");

%% ===================== 局部函数 =====================
function y = preprocessEEGDisplay(x, fs)
% x: N × channels，单位 uV
% y: 预处理后数据，单位 uV
%
% 处理流程：
% 1. 去 DC
% 2. 去线性趋势
% 3. 1 秒移动平均去慢漂
% 4. 50 Hz notch

    y = x;

    %% 1. 去 DC
    y = y - mean(y, 1, "omitnan");

    %% 2. 去线性趋势
    for ch = 1:size(y, 2)
        v = y(:, ch);
        valid = ~isnan(v);

        if sum(valid) > 5
            v(valid) = detrend(v(valid));
        end

        y(:, ch) = v;
    end

    %% 3. 1秒移动平均去慢漂
    win = max(3, round(1.0 * fs));

    for ch = 1:size(y, 2)
        v = y(:, ch);
        valid = ~isnan(v);

        if sum(valid) > win
            baseline = movmean(v(valid), win);
            v(valid) = v(valid) - baseline;
        end

        y(:, ch) = v;
    end

    %% 4. 50 Hz notch
    notchFreq = 50;

    if notchFreq > 0 && notchFreq < fs/2
        r = 0.95;
        theta = 2*pi*notchFreq/fs;

        b = [1, -2*cos(theta), 1];
        a = [1, -2*r*cos(theta), r^2];

        for ch = 1:size(y, 2)
            v = y(:, ch);
            valid = ~isnan(v);

            if sum(valid) > 10
                v(valid) = filter(b, a, v(valid));
            end

            y(:, ch) = v;
        end
    end
end

function cleanupContinuousEEG(txChar, stopCmd, rawFID, processedFID)
% 异常退出或 Ctrl+C 时：
% 1. 尽量发送 STOP，让硬件停止记录
% 2. 关闭文件
% 3. 不 unsubscribe，不 clear BLE，尽量保持蓝牙连接

    try
        write(txChar, stopCmd, "withoutresponse");
        pause(0.2);
        disp("异常退出：已尝试发送 STOP: AA 32 55");
    catch
    end

    try
        fclose(rawFID);
    catch
    end

    try
        fclose(processedFID);
    catch
    end
end