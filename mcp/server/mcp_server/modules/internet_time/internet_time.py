from core.module_interface import ModuleInterface
from typing import Dict, List, Tuple, Any, Optional, Union
import requests
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime  # 用于解析 HTTP Date 头


class InternetTime(ModuleInterface):
    """
    InternetTime 模块
    """

    def get_info(self):
        """
        获取模块信息

        Returns:
            dict: 模块信息
        """
        return {
            "name": "InternetTime",
            "version": "1.0.1",  # 版本号更新
            "description": "获取联网的真实日期，时间与周几信息（通过 HTTP 头）。",
            "author": "Weilin Shen"
        }

    def register(self, server):
        """
        向MCP服务器注册功能

        Args:
            server: FastMCP服务器实例
        """

        @server.tool()
        def get_internet_time(server: str = "https://www.baidu.com"):
            """
            通过 HTTP 头获取标准时间信息（如百度首页的 Date 响应头），包括日期、时间、星期几。
            使用举例：
            - 今天的日期
            - 现在的时间
            - 今天星期几

            :param server: HTTP 服务器地址，默认为 https://www.baidu.com
            :return: 包含当前日期时间、星期几以及时区的信息字典，如果请求失败则返回 {"error": <error message>}
            """
            try:
                response = requests.head(server, timeout=10)
                response.raise_for_status()
                date_str = response.headers.get('Date')

                if not date_str:
                    print("响应头中未找到 Date 字段")
                    return {"error": "无法从响应头获取时间信息"}

                # 解析 RFC 1123 格式的日期字符串（如：Tue, 05 Aug 2025 06:30:00 GMT）
                dt_utc = parsedate_to_datetime(date_str)

                # 转换为北京时间（UTC+8）
                dt_beijing = dt_utc + timedelta(hours=8)

                # 获取星期几
                weekday_str = get_weekday(dt_beijing)

                time_info = {
                    "datetime": dt_beijing.strftime('%Y-%m-%d %H:%M:%S'),
                    "weekday": weekday_str,
                    "timezone": "北京时间",
                    "source": f"HTTP Date header from {server}"
                }

                return time_info

            except requests.exceptions.RequestException as e:
                print(f"HTTP 请求失败: {e}")
                return {"error": f"HTTP 请求失败: {str(e)}"}
            except Exception as e:
                print(f"解析时间时发生错误: {e}")
                return {"error": f"时间解析失败: {str(e)}"}

        @server.tool()
        def get_weekday(dt: datetime) -> str:
            """
            获取指定 datetime 对象是星期几，返回中文格式（如 星期一）

            :param dt: datetime 时间对象
            :return: 中文表示的星期几
            """
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            return weekdays[dt.weekday()]

        @server.tool()
        def shift_time(
                base_time: datetime,
                days: int = 0,
                hours: int = 0,
                minutes: int = 0,
                seconds: int = 0
        ) -> datetime:
            """
            返回 base_time 偏移指定天数、小时数、分钟数、秒数后的时间。
            应用场景：精确计算偏移后的新日期时间。

            :param base_time: 原始 datetime 时间对象
            :param days: 偏移的天数（+ 表示未来，- 表示过去）
            :param hours: 偏移的小时数
            :param minutes: 偏移的分钟数
            :param seconds: 偏移的秒数
            :return: 新的 datetime 对象
            """
            return base_time + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
