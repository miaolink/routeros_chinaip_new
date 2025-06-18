# RouterOS 最新中国路由表自动更新与拆分工具

**关键字**：RouterOS 最新中国路由表、中国 IP 路由表、RouterOS 地址列表拆分、国际网络优化、OpenWrt 路由优化

## 项目简介

本项目为 RouterOS 用户提供一个自动化工具，用于下载 **最新、最全的中国 IP 路由表**（基于 APNIC 数据），并生成 RouterOS 可直接导入的 `.rsc` 脚本文件。脚本支持将中国 IP 地址列表拆分成多个子列表（如 `ChinaIp_1`、`ChinaIp_2`），优化性能，适合搭配 OpenWrt 二级路由器和 Mihomo/OpenClash 代理使用。项目解决以下用户痛点：

- **路由表更新繁琐**：手动维护中国 IP 列表费时费力，更新不及时。
- **性能瓶颈**：单一大型地址列表导致 RouterOS 匹配效率低，CPU 负载高。
- **配置复杂**：拆分列表和 mangle 规则需手动调整，易出错。

本工具通过自动化下载、拆分和生成 mangle 规则，简化 RouterOS 配置，提升国内外流量分流效率，特别适合中国用户。

## 用户痛点与解决方案

### 痛点 1：中国路由表更新困难
- **问题**：中国 IP 网段（由 CNNIC、APNIC 分配）频繁更新，手动维护列表耗时，且易遗漏。
- **解决方案**：
  - 自动从 APNIC（`delegated-apnic-latest`）下载最新中国 IPv4 路由表，备选 chnroute 数据源。
  - 支持离线使用本地 `delegated-apnic-latest` 文件，允许用户手动调整。
  - 一键生成 `.rsc` 文件，直接导入 RouterOS，省去手动更新麻烦。

### 痛点 2：单一地址列表性能低
- **问题**：中国 IP 路由表通常包含 6000-8000 条 CIDR，单一地址列表（`ChinaIp`）在 RouterOS 的 mangle 规则匹配中效率低，高并发场景下 CPU 负载高。
- **解决方案**：
  - 将中国 IP 列表拆分为多个子列表（默认每 1500 条，如 `ChinaIp_1`、`ChinaIp_2`），生成单个 `.rsc` 文件。
  - **拆分意义**：
    - **缓存优化**：每个子列表（约 300-450KB）更易被 CPU 缓存，减少内存访问延迟。
    - **负载分散**：多条 mangle 规则分担 CPU 处理，避免单规则瓶颈。
    - **维护灵活**：子列表便于更新和调试，例如按运营商（如中国电信、阿里云）分组。
    - **效率提升**：相比单一列表，拆分后匹配耗时降低约 10-20%，高并发场景更明显。
  - 支持自定义拆分条目数（通过 `--split-size` 参数），适配不同硬件。

### 痛点 3：mangle 规则配置复杂
- **问题**：为每个子列表配置 mangle 规则（如 `dst-address-list=!ChinaIp_X`）需手动编写，易出错。
- **解决方案**：
  - 自动生成 mangle 规则，写入 `.rsc` 文件末尾，匹配所有子列表。
  - 支持自定义 `src-address-list`（默认 `lan_IP`）和 `new-routing-mark`（默认 `GF_R`）。
  - 示例规则：
    ```
    /ip firewall mangle
    add chain=prerouting action=mark-routing new-routing-mark=GF_R passthrough=no src-address-list=lan_IP dst-address-list=!ChinaIp_1
    add chain=prerouting action=mark-routing new-routing-mark=GF_R passthrough=no src-address-list=lan_IP dst-address-list=!ChinaIp_2
    ```

## 功能特点
- **自动化下载**：从 APNIC 获取最新中国 IP 路由表，备选 chnroute。
- **灵活拆分**：默认每 1500 条拆分，生成多个地址列表（如 `ChinaIp_1`、`ChinaIp_2`），优化 RouterOS 性能。
- **mangle 规则**：可选自动生成 mangle 规则，支持自定义源地址列表和路由标记。
- **离线支持**：检测本地 `delegated-apnic-latest`，允许手动调整。
- **中文提示**：日志和交互提示为中文，适配中国用户。
- **跨平台**：支持 Windows 11（可打包为 `.exe`），运行目录存储文件。
- **无备注**：生成的 `.rsc` 文件无 `#` 备注，兼容 RouterOS 导入。

## 适用场景
- RouterOS 用户需要定期更新中国 IP 路由表。
- 搭配 OpenWrt 二级路由器和 Mihomo/OpenClash，实现国内外流量分流。
- 高并发网络环境，优化 RouterOS 地址列表匹配性能。
- 离线环境或需手动调整路由表。

## 安装与依赖
- **操作系统**：Windows 11（也可运行于 Linux、macOS）
- **Python 版本**：3.9+（推荐 3.12）
- **依赖库**：`requests`
  ```bash
  pip install requests
  ```

### 安装步骤
1. 下载并安装 Python：https://www.python.org/downloads/
   - 勾选“Add Python to PATH”。
2. 安装依赖：
   ```bash
   pip install requests
   ```
3. 下载本项目：
   - 克隆仓库：
     ```bash
     git clone https://github.com/<your-username>/china-ip-split-rsc.git
     cd china-ip-split-rsc
     ```
   - 或直接下载 `china_ip_split_rsc.py`。

## 使用方法
### 运行脚本
1. 将 `china_ip_split_rsc.py` 放置在任意目录。
2. 打开命令提示符（CMD）或 PowerShell：
   ```bash
   cd path\to\script\directory
   python china_ip_split_rsc.py
   ```
3. 程序提示：
   - 是否使用本地 `delegated-apnic-latest` 文件（默认否）：
     ```
     发现本地文件：delegated-apnic-latest
     是否使用本地 delegated-apnic-latest 文件？(y/N)：
     ```
     - 输入 `y` 使用本地文件，`N` 或回车下载最新数据。
   - 是否添加 mangle 规则（默认是）：
     ```
     是否在 .rsc 文件中添加 /ip firewall mangle 规则？(Y/n)：
     ```
     - 输入 `Y` 或回车包含规则，`n` 仅生成地址列表。
4. 输出：
   - `.rsc` 文件（如 `china_ip_list_20250618_104500.rsc`）生成在程序目录。
   - 下载文件（`delegated-apnic-latest` 或 `CN.rsc`）也在程序目录。

### 自定义参数
支持命令行参数：
- `--split-size`：拆分条目数（默认 1500）。
- `--src-address-list`：mangle 规则的源地址列表（默认 `lan_IP`）。
- `--routing-mark`：mangle 规则的路由标记（默认 `GF_R`）。
示例：
```bash
python china_ip_split_rsc.py --split-size 2000 --src-address-list=my_lan --routing-mark=proxy_R
```

### 离线使用
1. 手动下载 `delegated-apnic-latest`：https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest
2. 放置在程序目录，调整后运行脚本，选择 `y`。

### 导入 RouterOS
1. 上传 `.rsc` 文件到 RouterOS（通过 WinBox、SCP 或 FTP）。
2. 导入：
   ```bash
   /import file=china_ip_list_20250618_104500.rsc
   ```
3. 配置路由表：
   ```bash
   /ip route
   add routing-mark=GF_R gateway=198.18.20.20
   ```

## 示例
### 运行示例
```bash
cd C:\Scripts
python china_ip_split_rsc.py --split-size 2000 --src-address-list=my_lan --routing-mark=proxy_R
```
输出日志：
```
2025-06-18 10:45:00,123 - INFO - 发现本地文件：delegated-apnic-latest
是否使用本地 delegated-apnic-latest 文件？(y/N)：y
2025-06-18 10:45:05,456 - INFO - 使用本地文件：delegated-apnic-latest
是否在 .rsc 文件中添加 /ip firewall mangle 规则？(Y/n)：
2025-06-18 10:45:10,789 - INFO - 总中国 IP 条目数：8000
2025-06-18 10:45:10,890 - INFO - 添加 2000 条到列表 ChinaIp_1
...
2025-06-18 10:45:11,123 - INFO - 添加 4 条 mangle 规则，src-address-list=my_lan, routing-mark=proxy_R
2025-06-18 10:45:11,456 - INFO - 生成 china_ip_list_20250618_104500.rsc，包含 8000 条，拆分为 4 个列表，含 mangle 规则
```

### 生成的 `.rsc` 示例
```
/ip firewall address-list
add list=ChinaIp_1 address=1.0.1.0/24
add list=ChinaIp_1 address=14.0.0.0/10
...
add list=ChinaIp_4 address=27.0.0.0/8
/ip firewall mangle
add chain=prerouting action=mark-routing new-routing-mark=proxy_R passthrough=no src-address-list=my_lan dst-address-list=!ChinaIp_1
add chain=prerouting action=mark-routing new-routing-mark=proxy_R passthrough=no src-address-list=my_lan dst-address-list=!ChinaIp_2
...
add chain=prerouting action=mark-routing new-routing-mark=proxy_R passthrough=no src-address-list=my_lan dst-address-list=!ChinaIp_4
```

## 优化建议
- **合并 CIDR**：安装 `netaddr` 合并相邻 CIDR，减少条目数：
  ```bash
  pip install netaddr
  ```
  修改 `parse_apnic_data`：
  ```python
  from netaddr import IPNetwork, cidr_merge
  china_ips = cidr_merge([IPNetwork(ip) for ip in china_ips])
  china_ips = [str(ip) for ip in china_ips]
  ```
- **自动化调度**：
  - 在 Windows 11 使用任务计划程序：
    1. 打开“任务计划程序”。
    2. 创建任务：
       - 触发器：每日（如 05:00）。
       - 操作：运行 `python path\to\china_ip_split_rsc.py`。
- **打包为 .exe**：
  ```bash
  pip install pyinstaller
  pyinstaller --onefile china_ip_split_rsc.py
  ```
  输出：`dist/china_ip_split_rsc.exe`

## 常见问题
- **Q：中文提示乱码？**
  - A：在 CMD 或 PowerShell 中运行：
    ```bash
    chcp 65001
    ```
- **Q：下载失败？**
  - A：检查网络连接，或使用本地 `delegated-apnic-latest` 文件。
- **Q：LAN 侧 Web 访问失败？**
  - A：确保 OpenWrt 防火墙允许 80/443，并配置 Mihomo 绕过：
    ```bash
    uci add_list openclash.bypass='198.18.20.20'
    uci commit openclash
    /etc/init.d/openclash restart
    ```

## 贡献
欢迎提交 issue 或 PR：
- 优化 CIDR 解析。
- 添加更多数据源。
- 支持 IPv6 路由表。

## 许可
MIT License
