import requests
import ipaddress
import os
import logging
import argparse
from datetime import datetime

# 配置日志（中文提示）
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# 配置
APNIC_URL = "https://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest"
CHNROUTE_URL = "https://raw.githubusercontent.com/ruijzhan/chnroute/master/CN.rsc"
APNIC_FILE = "delegated-apnic-latest"
CHNROUTE_FILE = "CN.rsc"
DEFAULT_SPLIT_SIZE = 1500  # 默认每 1500 条拆分
LIST_NAME_PREFIX = "ChinaIp_"
OUTPUT_FILE = "china_ip_list.rsc"
DEFAULT_SRC_ADDRESS_LIST = "lan_IP"
DEFAULT_ROUTING_MARK = "GF_R"

def get_script_dir():
    """获取程序运行目录"""
    return os.path.dirname(os.path.abspath(__file__))

def prompt_use_local_file(filename):
    """提示用户是否使用本地文件，默认否"""
    if os.path.exists(os.path.join(get_script_dir(), filename)):
        logger.info(f"发现本地文件：{filename}")
        while True:
            choice = input(f"是否使用本地 {filename} 文件？(y/N)：").strip().lower()
            if choice in ['', 'n']:
                return False
            elif choice == 'y':
                return True
            logger.warning("输入无效，请输入 'y' 或 'N'")
    return False

def prompt_for_mangle():
    """提示用户是否添加 mangle 规则，默认是"""
    while True:
        choice = input("是否在 .rsc 文件中添加 /ip firewall mangle 规则？(Y/n)：").strip().lower()
        if choice in ['', 'y']:
            return True
        elif choice == 'n':
            return False
        logger.warning("输入无效，请输入 'Y' 或 'n'")

def read_local_file(filename):
    """读取本地文件"""
    try:
        with open(os.path.join(get_script_dir(), filename), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取本地文件 {filename} 失败：{e}")
        return None

def download_file(url, filename):
    """下载文件到程序运行目录"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(os.path.join(get_script_dir(), filename), 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"从 {url} 下载到 {filename}")
        return response.text
    except requests.RequestException as e:
        logger.error(f"下载 {url} 失败：{e}")
        return None

def parse_apnic_data(data):
    """解析 APNIC 数据，提取中国 IPv4 CIDR"""
    china_ips = []
    for line in data.splitlines():
        if line.startswith('#') or not line:
            continue
        parts = line.split('|')
        if len(parts) < 7 or parts[1] != 'CN' or parts[2] != 'ipv4':
            continue
        ip_start = parts[3]
        count = int(parts[4])
        try:
            network = ipaddress.ip_network(f"{ip_start}/{32 - (count.bit_length() - 1)}")
            china_ips.append(str(network))
        except ValueError as e:
            logger.warning(f"无效 CIDR：{ip_start}/{count}，错误：{e}")
    return sorted(set(china_ips))

def parse_chnroute_data(data):
    """解析 chnroute 的 .rsc 文件，提取 CIDR"""
    china_ips = []
    for line in data.splitlines():
        if line.strip().startswith('add list='):
            parts = line.split('address=')
            if len(parts) > 1:
                cidr = parts[1].split()[0].strip()
                try:
                    ipaddress.ip_network(cidr)
                    china_ips.append(cidr)
                except ValueError:
                    logger.warning(f"chnroute 中无效 CIDR：{cidr}")
    return sorted(set(china_ips))

def write_rsc(china_ips, split_size, list_name_prefix, add_mangle, src_address_list, routing_mark):
    """生成单个 .rsc 文件，拆分列表名称，无备注，mangle 规则在最下方"""
    total_ips = len(china_ips)
    logger.info(f"总中国 IP 条目数：{total_ips}")
    if total_ips == 0:
        logger.error("无 IP 地址可处理")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(get_script_dir(), f"{OUTPUT_FILE.replace('.rsc', f'_{timestamp}.rsc')}")
    with open(filename, 'w', encoding='utf-8') as f:
        # 写入地址列表
        f.write("/ip firewall address-list\n")
        list_names = []
        for i in range(0, total_ips, split_size):
            chunk = china_ips[i:i + split_size]
            list_name = f"{list_name_prefix}{i//split_size + 1}"
            list_names.append(list_name)
            for ip in chunk:
                f.write(f"add list={list_name} address={ip}\n")
            logger.info(f"添加 {len(chunk)} 条到列表 {list_name}")

        # 写入 mangle 规则（若启用）
        if add_mangle:
            f.write("/ip firewall mangle\n")
            for list_name in list_names:
                f.write(f"add chain=prerouting action=mark-routing new-routing-mark={routing_mark} passthrough=yes src-address-list={src_address_list} dst-address-list=!{list_name}\n")
            logger.info(f"添加 {len(list_names)} 条 mangle 规则，src-address-list={src_address_list}, routing-mark={routing_mark}")

    logger.info(f"生成 {filename}，包含 {total_ips} 条，拆分为 {total_ips//split_size + 1} 个列表{'，含 mangle 规则' if add_mangle else ''}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="下载并拆分中国 IP 列表为单个 RouterOS .rsc 文件")
    parser.add_argument('--split-size', type=int, default=DEFAULT_SPLIT_SIZE, help='每个地址列表的 IP 条目数')
    parser.add_argument('--src-address-list', default=DEFAULT_SRC_ADDRESS_LIST, help='mangle 规则的 src-address-list')
    parser.add_argument('--routing-mark', default=DEFAULT_ROUTING_MARK, help='mangle 规则的 new-routing-mark')
    args = parser.parse_args()

    # 检查本地 APNIC 文件
    data = None
    if prompt_use_local_file(APNIC_FILE):
        data = read_local_file(APNIC_FILE)
        if data:
            logger.info(f"使用本地文件：{APNIC_FILE}")
            china_ips = parse_apnic_data(data)
        else:
            logger.error("本地文件无效，尝试下载")
    else:
        # 下载 APNIC 数据
        logger.info(f"从 APNIC 下载：{APNIC_URL}")
        data = download_file(APNIC_URL, APNIC_FILE)
        if data:
            china_ips = parse_apnic_data(data)
        else:
            # 备选 chnroute
            logger.info(f"回退到 chnroute：{CHNROUTE_URL}")
            data = download_file(CHNROUTE_URL, CHNROUTE_FILE)
            if data:
                china_ips = parse_chnroute_data(data)
            else:
                logger.error("所有下载源均失败")
                return

    # 提示是否添加 mangle 规则
    add_mangle = prompt_for_mangle()

    # 生成 .rsc 文件
    write_rsc(china_ips, args.split_size, LIST_NAME_PREFIX, add_mangle, args.src_address_list, args.routing_mark)

if __name__ == "__main__":
    main()
