"""
钓鱼小游戏
功能：点击开始后等待上钩，出现按键序列(QTE)及时按对即可钓鱼成功；
    卖鱼赚钱，买鱼饵/鱼竿/礼物，推进林汐事件与好感。
"""
import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time
import sys
import ctypes
import datetime
import json
import os


# ==========================
# DPI 设置
# ==========================
class DPIManager:
    @staticmethod
    def setup(root):
        if sys.platform == 'win32':
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
                scalefactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
                root.tk.call('tk', 'scaling', scalefactor / 75)
            except Exception as e:
                print(f"DPI 设置失败: {e}")


# ==========================
# 鱼类数据定义
# ==========================
# 鱼的稀有度定义
RARITY_COMMON = "杂鱼~"      # 常见，概率高，时间短
RARITY_UNCOMMON = "冬雪莲"  # 冬雪莲，概率中等，时间中等
RARITY_RARE = "稀有"        # 稀有，概率低，时间长
RARITY_EPIC = "史诗"        # 史诗，概率很低，时间很长

# 小溪的鱼类配置（8种鱼，无史诗级，重量较小）
FISH_CONFIG_STREAM = [
    # (名称, 稀有度, 最小重量kg, 最大重量kg, 基础概率权重, 基础等待时间秒)
    ("小鲫鱼", RARITY_COMMON, 0.1, 0.4, 40, (3, 8)),
    ("小鲤鱼", RARITY_COMMON, 0.15, 0.6, 35, (4, 10)),
    ("泥鳅", RARITY_COMMON, 0.05, 0.25, 25, (2, 6)),
    ("草鱼", RARITY_UNCOMMON, 0.4, 1.2, 20, (8, 15)),
    ("鲶鱼", RARITY_UNCOMMON, 0.6, 1.5, 15, (10, 20)),
    ("黑鱼", RARITY_UNCOMMON, 0.5, 1.3, 12, (12, 25)),
    ("鳊鱼", RARITY_RARE, 0.8, 2.0, 8, (20, 35)),
    ("青鱼", RARITY_RARE, 1.0, 2.5, 5, (25, 45)),
]

# 河流的鱼类配置（10种鱼，包含史诗级，重量更大，common概率降低）
FISH_CONFIG_RIVER = [
    # (名称, 稀有度, 最小重量kg, 最大重量kg, 基础概率权重, 基础等待时间秒)
    ("小鲫鱼", RARITY_COMMON, 0.2, 0.6, 30, (3, 8)),  # 概率降低，重量增加
    ("小鲤鱼", RARITY_COMMON, 0.3, 1.0, 25, (4, 10)),  # 概率降低，重量增加
    ("泥鳅", RARITY_COMMON, 0.1, 0.4, 20, (2, 6)),     # 概率降低，重量增加
    ("草鱼", RARITY_UNCOMMON, 0.8, 2.5, 22, (8, 15)),   # 重量增加
    ("鲶鱼", RARITY_UNCOMMON, 1.2, 3.5, 18, (10, 20)),  # 重量增加
    ("黑鱼", RARITY_UNCOMMON, 1.0, 3.0, 15, (12, 25)),  # 重量增加
    ("鳊鱼", RARITY_RARE, 1.5, 4.0, 10, (20, 35)),      # 重量增加
    ("青鱼", RARITY_RARE, 2.0, 5.5, 8, (25, 45)),       # 重量增加
    ("翘嘴鱼", RARITY_EPIC, 3.0, 7.0, 4, (35, 60)),     # 重量增加
    ("野生大草鱼", RARITY_EPIC, 4.0, 10.0, 3, (40, 60)), # 重量增加
]

# 湖泊的鱼类配置（8种鱼，写实常见鱼类，包含史诗级）
FISH_CONFIG_LAKE = [
    # (名称, 稀有度, 最小重量kg, 最大重量kg, 基础概率权重, 基础等待时间秒)
    ("白鲢", RARITY_COMMON, 0.5, 2.0, 40, (3, 8)),
    ("花鲢", RARITY_COMMON, 0.8, 2.5, 35, (4, 10)),
    ("湖蟹", RARITY_UNCOMMON, 0.2, 0.8, 25, (8, 15)),
    ("湖鲈鱼", RARITY_UNCOMMON, 1.0, 3.0, 20, (10, 20)),
    ("大闸蟹", RARITY_RARE, 0.3, 1.5, 12, (20, 35)),
    ("大鲢鱼", RARITY_RARE, 2.0, 5.0, 8, (25, 45)),
    ("野生大鲈鱼", RARITY_EPIC, 3.5, 7.0, 3, (40, 60)),
    ("湖泊巨鲶", RARITY_EPIC, 6.0, 12.0, 2, (45, 60)),
]

# 地点鱼类配置映射
LOCATION_FISH_CONFIG = {
    "小溪": FISH_CONFIG_STREAM,
    "河流": FISH_CONFIG_RIVER,  # 河流专属鱼类（包含史诗级）
    "湖泊": FISH_CONFIG_LAKE,  # 湖泊专属鱼类
}


# ==========================
# 经济与道具配置
# ==========================
BAIT_CONFIG = {
    "普通鱼饵": {
        "price": 0,
        "rarity_bonus": {RARITY_COMMON: 1.0, RARITY_UNCOMMON: 1.0, RARITY_RARE: 1.0, RARITY_EPIC: 1.0},
        "wait_multiplier": 1.0
    },
    "高级蚯蚓": {
        "price": 80,
        "rarity_bonus": {RARITY_COMMON: 0.9, RARITY_UNCOMMON: 1.1, RARITY_RARE: 1.25, RARITY_EPIC: 1.1},
        "wait_multiplier": 0.9
    },
    "路亚假饵": {
        "price": 120,
        "rarity_bonus": {RARITY_COMMON: 0.85, RARITY_UNCOMMON: 1.0, RARITY_RARE: 1.1, RARITY_EPIC: 1.35},
        "wait_multiplier": 0.95
    }
}

ROD_CONFIG = {
    "木质竿": {"price": 0, "window": 1.0},
    "碳素竿": {"price": 300, "window": 1.4},
    "竞赛竿": {"price": 600, "window": 1.6}
}

GIFT_SHOP_ITEMS = {
    "奶茶": {"price": 60, "tags": ["甜", "饮品"]},
    "草莓蛋糕": {"price": 120, "tags": ["甜", "点心"]},
    "辣条": {"price": 40, "tags": ["辣", "零食"]},
    "相机冲印券": {"price": 90, "tags": ["纪念"]},
}

CRAFT_ITEMS = {
    "卡式炉": {"price": 180},
}

FISH_PRICE_PER_KG = {
    RARITY_COMMON: 12,
    RARITY_UNCOMMON: 20,
    RARITY_RARE: 38,
    RARITY_EPIC: 65,
}

# 经验系统配置
FISH_EXP_BASE = {
    RARITY_COMMON: 8,      # 杂鱼~基础经验
    RARITY_UNCOMMON: 20,   # 冬雪莲基础经验
    RARITY_RARE: 50,       # 稀有基础经验
    RARITY_EPIC: 120,      # 史诗基础经验
}

# 升级所需经验表（从当前等级升到下一级）
LEVEL_UP_EXP = {
    1: 50,    # 1->2级
    2: 100,   # 2->3级
    3: 200,   # 3->4级（解锁河流）
    4: 350,   # 4->5级
    5: 550,   # 5->6级
    6: 800,   # 6->7级（解锁湖泊）
    7: 1100,  # 7->8级
    8: 1450,  # 8->9级
    9: 1850,  # 9->10级（满级）
}

# 地点解锁等级要求
LOCATION_UNLOCK_LEVEL = {
    "小溪": 1,   # 初始解锁
    "河流": 4,   # 4级解锁
    "湖泊": 7,   # 7级解锁
}

WEATHER_OPTIONS = [
    ("晴朗", 1.0, {RARITY_EPIC: 1.0, RARITY_RARE: 1.0}),
    ("小雨", 0.78, {RARITY_RARE: 1.1, RARITY_EPIC: 1.05}),
    ("暴晒", 1.22, {RARITY_COMMON: 1.15, RARITY_EPIC: 1.15}),
]

TIME_SLOTS = [
    ("清晨", 0.9, {RARITY_UNCOMMON: 1.05}),
    ("正午", 1.15, {RARITY_EPIC: 1.12}),
    ("黄昏", 0.95, {RARITY_RARE: 1.1}),
]

DAILY_REQUEST_POOL = [
    {"desc": "今天想喝鲫鱼汤", "prefer": "小鲫鱼"},
    {"desc": "想吃点甜的", "tag": "甜"},
    {"desc": "想试试烤鱼", "tag": "热食"},
    {"desc": "想解馋吃辣条", "prefer": "辣条"},
]


# ==========================
# 统计文件管理
# ==========================
STATS_FILE = "fishing_stats.json"

def _default_inventory_state():
    return {
        'fish_bag': [],  # 每条鱼记录 {name, weight, rarity}
        'money': 0,
        'exp': 0,        # 当前经验值
        'level': 1,      # 当前等级（1-10）
        'day': 1,        # 当前天数（从第一天开始）
        'last_level_up_day': 0,  # 最后一次升级的天数（0表示从未升级）
        'selected_bait': '普通鱼饵',
        'owned_rods': ['木质竿'],
        'equipped_rod': '木质竿',
        'bait_items': {name: (3 if name == '普通鱼饵' else 0) for name in BAIT_CONFIG.keys()},
        'gift_items': {name: 0 for name in GIFT_SHOP_ITEMS.keys()},
        'craft_items': {name: 0 for name in CRAFT_ITEMS.keys()},
        'cooked_items': {"烤鱼": 0},
    }

def _default_student_state():
    """默认的女高中生事件状态"""
    return {
        'name': '林汐',
        'met': False,
        'rescued': False,
        'trust': 0,
        'food_stock': 0.0,
        'encounter_rolls': 0,
        'last_gift_date': None,
        'daily_request': None,
        'daily_request_date': None
    }

def load_statistics():
    """从文件加载统计数据"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                student_state = data.get('student_state', _default_student_state())
                merged_state = _default_student_state()
                merged_state.update(student_state)

                inventory = data.get('inventory', _default_inventory_state())
                merged_inventory = _default_inventory_state()
                try:
                    # 深度合并计数字典
                    merged_inventory.update({k: v for k, v in inventory.items() if k in merged_inventory})
                    for key in ('bait_items', 'gift_items', 'craft_items', 'cooked_items'):
                        merged_inventory[key].update(inventory.get(key, {}))
                    # 鱼袋直接覆盖
                    merged_inventory['fish_bag'] = inventory.get('fish_bag', [])
                except Exception:
                    merged_inventory = _default_inventory_state()

                return data.get('fish_statistics', {}), merged_inventory, merged_state
        except Exception as e:
            print(f"加载统计数据失败: {e}")
            return {}, _default_inventory_state(), _default_student_state()
    return {}, _default_inventory_state(), _default_student_state()

def save_statistics(fish_statistics, inventory_state=None, student_state=None):
    """保存统计数据到文件"""
    try:
        data = {
            'fish_statistics': fish_statistics,
            'inventory': inventory_state or _default_inventory_state(),
            'student_state': student_state or _default_student_state(),
            'last_update': datetime.datetime.now().isoformat()
        }
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存统计数据失败: {e}")


# ==========================
# 游戏状态管理
# ==========================
class GameState:
    """游戏状态管理类，为后续扩展预留接口"""
    def __init__(self):
        # 当前游戏状态
        self.is_fishing = False  # 是否正在钓鱼
        self.is_waiting_for_bite = False  # 是否等待咬钩
        self.is_bite_occurred = False  # 是否已经咬钩
        self.catch_success = False  # 本次是否成功钓到鱼
        
        # 当前钓到的鱼信息
        self.current_fish = None  # 当前钓到的鱼（名称）
        self.current_fish_weight = None  # 当前钓到的鱼的重量
        
        # 从文件加载统计数据
        self.fish_statistics, inventory_state, student_state = load_statistics()
        
        # 预留扩展字段
        self.current_location = "小溪"  # 当前钓鱼地点（默认小溪）
        self.home_data = {}  # 家园数据（预留）
        self.student_state = student_state
        self.inventory = inventory_state
        self._ensure_student_state()
        self._ensure_inventory_state()
        
        # 初始化所有鱼的统计数据（如果文件中没有）
        self._init_fish_statistics()
    
    def _init_fish_statistics(self):
        """初始化所有鱼的统计数据"""
        for location, fish_list in LOCATION_FISH_CONFIG.items():
            for fish_name, _, _, _, _, _ in fish_list:
                if fish_name not in self.fish_statistics:
                    self.fish_statistics[fish_name] = {'count': 0, 'max_weight': 0.0}

    def _ensure_student_state(self):
        """兜底补齐女高中生事件状态"""
        merged = _default_student_state()
        try:
            merged.update(self.student_state or {})
        except Exception:
            pass
        self.student_state = merged

    def _ensure_inventory_state(self):
        """兜底补齐背包与金钱状态"""
        base = _default_inventory_state()
        try:
            inv = self.inventory or {}
        except Exception:
            inv = {}
        # 基本字段
        base.update({k: v for k, v in inv.items() if k in base})
        # 合并计数字典
        for key in ('bait_items', 'gift_items', 'craft_items', 'cooked_items'):
            try:
                base[key].update(inv.get(key, {}))
            except Exception:
                pass
        # 鱼袋
        base['fish_bag'] = inv.get('fish_bag', []) if isinstance(inv.get('fish_bag', []), list) else []
        self.inventory = base

    def register_student_encounter(self):
        """首次遇到林汐"""
        self.student_state['met'] = True
        self.student_state['encounter_rolls'] = self.student_state.get('encounter_rolls', 0)
        self.student_state['trust'] = max(self.student_state.get('trust', 0), 5)
        self.save_stats()

    def add_student_food(self, weight: float):
        """把钓到的鱼分享给林汐，返回更新信息"""
        if not self.student_state.get('met'):
            return {'trust_delta': 0, 'ready': False}
        self.student_state['food_stock'] = round(self.student_state.get('food_stock', 0.0) + weight, 2)
        trust_gain = 2 if weight >= 1.0 else 1
        before_trust = self.student_state.get('trust', 0)
        self.student_state['trust'] = min(100, before_trust + trust_gain)
        ready = self.student_state['food_stock'] >= 8.0 and not self.student_state.get('rescued')
        self.save_stats()
        return {
            'trust_delta': self.student_state['trust'] - before_trust,
            'trust': self.student_state['trust'],
            'food_stock': self.student_state['food_stock'],
            'ready': ready
        }

    def try_rescue_student(self):
        """满足条件后安排救援"""
        if not self.student_state.get('met'):
            return False
        if self.student_state.get('rescued'):
            return True
        if self.student_state.get('food_stock', 0) < 8.0:
            return False
        self.student_state['rescued'] = True
        self.student_state['trust'] = max(self.student_state.get('trust', 0), 40)
        self.save_stats()
        return True

    def boost_student_trust(self, amount: int = 3):
        """鼓励对话提升信任"""
        if not self.student_state.get('met'):
            return 0
        before = self.student_state.get('trust', 0)
        self.student_state['trust'] = min(100, before + amount)
        self.save_stats()
        return self.student_state['trust'] - before

    # ==========================
    # 经济、背包、道具
    # ==========================
    def get_money(self) -> float:
        return round(self.inventory.get('money', 0), 2)

    def add_money(self, amount: float):
        self.inventory['money'] = round(max(0, self.get_money() + amount), 2)
        self.save_stats()

    def spend_money(self, amount: float) -> bool:
        if self.get_money() >= amount:
            self.inventory['money'] = round(self.get_money() - amount, 2)
            self.save_stats()
            return True
        return False

    # ==========================
    # 天数系统
    # ==========================
    def get_day(self) -> int:
        """获取当前天数"""
        return self.inventory.get('day', 1)
    
    def add_day(self, amount: int = 1) -> int:
        """增加天数
        Args:
            amount: 增加的天数，默认为1
        Returns:
            新的天数
        """
        current_day = self.get_day()
        new_day = current_day + amount
        self.inventory['day'] = new_day
        self.save_stats()
        return new_day

    # ==========================
    # 经验与等级系统
    # ==========================
    def get_level(self) -> int:
        """获取当前等级"""
        return self.inventory.get('level', 1)
    
    def get_exp(self) -> int:
        """获取当前经验值"""
        return self.inventory.get('exp', 0)
    
    def get_exp_for_next_level(self) -> int:
        """获取升到下一级所需的经验值"""
        current_level = self.get_level()
        if current_level >= 10:
            return 0  # 已满级
        return LEVEL_UP_EXP.get(current_level, 0)
    
    def calculate_exp_gain(self, rarity: str, weight: float, min_weight: float = 0.1, max_weight: float = 1.0) -> int:
        """计算获得的经验值
        Args:
            rarity: 鱼的稀有度
            weight: 鱼的重量
            min_weight: 该类鱼的最小重量（用于计算重量加成）
            max_weight: 该类鱼的最大重量（用于计算重量加成）
        Returns:
            获得的经验值
        """
        # 基础经验值
        base_exp = FISH_EXP_BASE.get(rarity, 5)
        
        # 重量加成：重量越大，经验越多（基于重量在范围内的比例）
        # 最小重量时加成0.5，最大重量时加成1.5
        if max_weight > min_weight:
            weight_ratio = (weight - min_weight) / (max_weight - min_weight)
            weight_multiplier = 0.5 + weight_ratio * 1.0  # 0.5 到 1.5
        else:
            weight_multiplier = 1.0
        
        # 最终经验值 = 基础经验 * 重量加成（向下取整）
        exp_gain = int(base_exp * weight_multiplier)
        return max(1, exp_gain)  # 至少1点经验
    
    def add_exp(self, amount: int) -> dict:
        """添加经验值，并处理升级
        Returns:
            dict: {'exp_added': 添加的经验, 'leveled_up': 是否升级, 'new_level': 新等级, 'unlocked_location': 解锁的地点}
        """
        current_level = self.get_level()
        current_exp = self.get_exp()
        current_day = self.get_day()
        last_level_up_day = self.inventory.get('last_level_up_day', 0)
        
        # 如果已满级，不添加经验
        if current_level >= 10:
            return {'exp_added': 0, 'leveled_up': False, 'new_level': current_level, 'unlocked_location': None}
        
        # 如果今天已经升级过，不添加经验
        if last_level_up_day >= current_day:
            return {'exp_added': 0, 'leveled_up': False, 'new_level': current_level, 'unlocked_location': None, 'note': '今天已经升级过了，明天再来获得经验吧！'}
        
        # 添加经验
        new_exp = current_exp + amount
        new_level = current_level
        leveled_up = False
        unlocked_location = None
        
        # 检查是否升级（每天最多升级一次）
        while new_level < 10:
            exp_needed = LEVEL_UP_EXP.get(new_level, 0)
            if exp_needed == 0:  # 已满级或配置错误
                break
            if new_exp >= exp_needed:
                new_exp -= exp_needed
                new_level += 1
                leveled_up = True
                # 记录升级的天数
                self.inventory['last_level_up_day'] = current_day
                # 检查是否解锁了新地点
                for location, unlock_level in LOCATION_UNLOCK_LEVEL.items():
                    if new_level == unlock_level:
                        unlocked_location = location
                # 每天只能升级一次，所以升级后立即退出循环
                break
            else:
                break
        
        # 更新状态
        self.inventory['exp'] = new_exp
        self.inventory['level'] = new_level
        self.save_stats()
        
        return {
            'exp_added': amount,
            'leveled_up': leveled_up,
            'new_level': new_level,
            'unlocked_location': unlocked_location
        }
    
    def is_location_unlocked(self, location: str) -> bool:
        """检查地点是否已解锁"""
        required_level = LOCATION_UNLOCK_LEVEL.get(location, 1)
        return self.get_level() >= required_level

    def add_caught_fish(self, fish_name: str, weight: float, rarity: str):
        self.inventory.setdefault('fish_bag', []).append({
            'name': fish_name,
            'weight': weight,
            'rarity': rarity
        })
        self.save_stats()

    def sell_all_fish(self):
        bag = self.inventory.get('fish_bag', [])
        earnings = 0.0
        for fish in bag:
            rarity = fish.get('rarity', RARITY_COMMON)
            price_per = FISH_PRICE_PER_KG.get(rarity, 10)
            earnings += price_per * fish.get('weight', 0)
        sold_count = len(bag)
        self.inventory['fish_bag'] = []
        self.add_money(earnings)
        return earnings, sold_count

    def remove_one_fish(self, fish_name: str):
        bag = self.inventory.get('fish_bag', [])
        for idx, fish in enumerate(bag):
            if fish.get('name') == fish_name:
                bag.pop(idx)
                self.save_stats()
                return fish
        return None

    def fish_bag_summary(self):
        summary = {}
        for fish in self.inventory.get('fish_bag', []):
            name = fish.get('name')
            summary.setdefault(name, {'count': 0, 'total_weight': 0.0, 'rarity': fish.get('rarity', RARITY_COMMON)})
            summary[name]['count'] += 1
            summary[name]['total_weight'] += fish.get('weight', 0.0)
        return summary

    def get_owned_rods(self):
        return self.inventory.get('owned_rods', ['木质竿'])

    def equip_rod(self, rod_name: str) -> bool:
        if rod_name in self.get_owned_rods():
            self.inventory['equipped_rod'] = rod_name
            self.save_stats()
            return True
        return False

    def select_bait(self, bait_name: str) -> bool:
        if bait_name in BAIT_CONFIG:
            self.inventory['selected_bait'] = bait_name
            self.save_stats()
            return True
        return False

    def consume_bait(self) -> str:
        bait = self.inventory.get('selected_bait', '普通鱼饵')
        if bait == '普通鱼饵':
            return bait
        count = self.inventory['bait_items'].get(bait, 0)
        if count > 0:
            self.inventory['bait_items'][bait] = count - 1
            self.save_stats()
            return bait
        # 如果没货自动回退
        self.inventory['selected_bait'] = '普通鱼饵'
        self.save_stats()
        return '普通鱼饵'

    def acquire_item(self, item_name: str, count: int = 1):
        if item_name in BAIT_CONFIG:
            self.inventory['bait_items'][item_name] = self.inventory['bait_items'].get(item_name, 0) + count
        elif item_name in GIFT_SHOP_ITEMS:
            self.inventory['gift_items'][item_name] = self.inventory['gift_items'].get(item_name, 0) + count
        elif item_name in CRAFT_ITEMS:
            self.inventory['craft_items'][item_name] = self.inventory['craft_items'].get(item_name, 0) + count
        elif item_name == "烤鱼":
            self.inventory['cooked_items'][item_name] = self.inventory['cooked_items'].get(item_name, 0) + count
        self.save_stats()

    def consume_item(self, item_name: str) -> bool:
        if item_name in BAIT_CONFIG:
            count = self.inventory['bait_items'].get(item_name, 0)
            if count > 0:
                self.inventory['bait_items'][item_name] = count - 1
                self.save_stats()
                return True
            return False
        if item_name in GIFT_SHOP_ITEMS:
            count = self.inventory['gift_items'].get(item_name, 0)
            if count > 0:
                self.inventory['gift_items'][item_name] = count - 1
                self.save_stats()
                return True
            return False
        if item_name in self.inventory.get('cooked_items', {}):
            count = self.inventory['cooked_items'].get(item_name, 0)
            if count > 0:
                self.inventory['cooked_items'][item_name] = count - 1
                self.save_stats()
                return True
        return False

    def cook_one_fish(self):
        """将任意一条鱼烤熟，需卡式炉"""
        if self.inventory['craft_items'].get('卡式炉', 0) <= 0:
            return False, "缺少卡式炉"
        if not self.inventory.get('fish_bag'):
            return False, "没有鱼可以烤"
        fish = self.inventory['fish_bag'].pop(0)
        self.acquire_item('烤鱼', 1)
        self.save_stats()
        return True, f"将 {fish.get('name', '鱼')} 烤成了热乎的烤鱼"

    def add_rod(self, rod_name: str):
        rods = self.inventory.setdefault('owned_rods', ['木质竿'])
        if rod_name not in rods:
            rods.append(rod_name)
        self.save_stats()

    def get_catch_window(self) -> float:
        rod = self.inventory.get('equipped_rod', '木质竿')
        rod_bonus = ROD_CONFIG.get(rod, {}).get('window', 1.0)
        trust_bonus = 0.1 if self.student_state.get('rescued') else 0.0
        return 1.0 * rod_bonus + trust_bonus

    def get_wait_time_multiplier(self) -> float:
        """根据伙伴和天气加成调整等待时间"""
        trust_factor = 1.0
        if self.student_state.get('rescued'):
            trust = self.student_state.get('trust', 0)
            trust_factor = max(0.6, 1 - trust * 0.0025)
        bait = self.inventory.get('selected_bait', '普通鱼饵')
        bait_factor = BAIT_CONFIG.get(bait, {}).get('wait_multiplier', 1.0)
        env_factor = getattr(self, 'current_environment_wait', 1.0)
        return trust_factor * bait_factor * env_factor

    def roll_environment(self):
        weather = random.choice(WEATHER_OPTIONS)
        time_slot = random.choice(TIME_SLOTS)
        self.current_weather = weather[0]
        self.current_time_slot = time_slot[0]
        self.current_environment_wait = weather[1] * time_slot[1]
        self.current_environment_rarity_bonus = {}
        self.current_environment_rarity_bonus.update(weather[2])
        self.current_environment_rarity_bonus.update(time_slot[2])

    def get_rarity_weight_multiplier(self, rarity: str) -> float:
        bait = self.inventory.get('selected_bait', '普通鱼饵')
        bait_bonus = BAIT_CONFIG.get(bait, {}).get('rarity_bonus', {}).get(rarity, 1.0)
        env_bonus = self.current_environment_rarity_bonus.get(rarity, 1.0) if hasattr(self, 'current_environment_rarity_bonus') else 1.0
        return bait_bonus * env_bonus

    # ==========================
    # 林汐：礼物、委托、情绪
    # ==========================
    def _today_str(self):
        return datetime.date.today().isoformat()

    def ensure_daily_request(self):
        today = self._today_str()
        if self.student_state.get('daily_request_date') != today:
            req = random.choice(DAILY_REQUEST_POOL)
            self.student_state['daily_request'] = req
            self.student_state['daily_request_date'] = today
            self.save_stats()
        return self.student_state.get('daily_request')

    def apply_mood_decay(self):
        last = self.student_state.get('last_gift_date')
        if not last:
            return 0
        try:
            last_day = datetime.date.fromisoformat(last)
            delta = (datetime.date.today() - last_day).days
            if delta > 2:
                decay = min(6, (delta - 2) * 2)
                before = self.student_state.get('trust', 0)
                self.student_state['trust'] = max(0, before - decay)
                self.save_stats()
                return before - self.student_state['trust']
        except Exception:
            return 0
        return 0

    def _set_gift_timestamp(self):
        self.student_state['last_gift_date'] = self._today_str()
        self.save_stats()

    def gift_to_student(self, name: str, tags=None, weight: float = 0.0):
        if not self.student_state.get('met'):
            return {'trust_delta': 0, 'note': '还未遇见林汐', 'success': False}
        
        # 检查今天是否已经送过礼物
        current_day = self.get_day()
        last_gift_day = self.student_state.get('last_gift_day', 0)
        if last_gift_day >= current_day:
            return {'trust_delta': 0, 'note': '今天已经送过礼物了，明天再来吧！', 'success': False}
        
        tags = tags or []
        like_tags = {"甜", "纪念", "热食"}
        dislike_tags = {"辣", "生鱼"}

        base_gain = 2
        if any(tag in like_tags for tag in tags):
            base_gain += 2
        if any(tag in dislike_tags for tag in tags):
            base_gain -= 3
        if weight >= 1.5:
            base_gain += 1

        daily_req = self.ensure_daily_request()
        if daily_req:
            prefer = daily_req.get('prefer')
            tag_pref = daily_req.get('tag')
            if prefer and prefer == name:
                base_gain += 2
            if tag_pref and tag_pref in tags:
                base_gain += 2

        before = self.student_state.get('trust', 0)
        self.student_state['trust'] = max(0, min(100, before + base_gain))
        self.student_state['food_stock'] = round(self.student_state.get('food_stock', 0.0) + weight, 2)
        # 记录今天送过礼物的天数（用于每日限制检查）
        self.student_state['last_gift_day'] = current_day
        # 同时记录实际日期（用于情绪衰减）
        self._set_gift_timestamp()
        self.save_stats()
        return {
            'trust_delta': self.student_state['trust'] - before,
            'trust': self.student_state['trust'],
            'food_stock': self.student_state['food_stock'],
            'success': True
        }
    
    def save_stats(self):
        """保存统计数据到文件"""
        save_statistics(self.fish_statistics, self.inventory, self.student_state)
    
    def reset_fishing_state(self):
        """重置钓鱼状态"""
        self.is_fishing = False
        self.is_waiting_for_bite = False
        self.is_bite_occurred = False
        self.catch_success = False
    
    def start_fishing(self):
        """开始钓鱼"""
        self.is_fishing = True
        self.is_waiting_for_bite = True
        self.is_bite_occurred = False
        self.catch_success = False
        self.current_fish = None
        self.current_fish_weight = None
    
    def on_bite(self):
        """咬钩事件"""
        self.is_bite_occurred = True
        self.is_waiting_for_bite = False
    
    def on_catch_success(self, fish_name: str, weight: float):
        """成功钓到鱼"""
        self.catch_success = True
        self.current_fish = fish_name
        self.current_fish_weight = weight
        
        # 更新统计数据
        if fish_name not in self.fish_statistics:
            self.fish_statistics[fish_name] = {'count': 0, 'max_weight': 0.0}
        
        self.fish_statistics[fish_name]['count'] += 1
        if weight > self.fish_statistics[fish_name]['max_weight']:
            self.fish_statistics[fish_name]['max_weight'] = weight
        
        # 自动保存统计数据
        self.save_stats()
    
    def on_catch_failed(self):
        """钓鱼失败"""
        self.catch_success = False
        self.current_fish = None
        self.current_fish_weight = None


# ==========================
# 钓鱼管理器
# ==========================
class FishingManager:
    """钓鱼逻辑管理类"""
    def __init__(self, game_state: GameState, root):
        self.game_state = game_state
        self.root = root
        self.fishing_thread = None
        self.bite_timer = None
        self.catch_window_timer = None
        
        # 当前选中的鱼（用于计算时间和概率）
        self.current_selected_fish = None
        self.current_bait_used = '普通鱼饵'
        self.qte_sequence = []
        self.qte_deadline = None
        
        # 钓鱼参数
        self.catch_window = 1.0  # 咬钩后的反应时间窗口（秒），后续根据鱼竿覆盖
        
        # 回调函数（由UI设置）
        self.on_bite_callback = None  # 咬钩时的回调，参数(qte_sequence)
        self.on_fishing_end_callback = None  # 钓鱼结束时的回调
    
    def _select_fish_by_probability(self, location: str):
        """根据概率选择要钓的鱼"""
        # 如果地点不存在，默认使用小溪
        fish_list = LOCATION_FISH_CONFIG.get(location, LOCATION_FISH_CONFIG["小溪"])
        
        # 计算总权重
        weighted_list = []
        total_weight = 0
        for fish_info in fish_list:
            rarity = fish_info[1]
            base_weight = fish_info[4]
            mult = self.game_state.get_rarity_weight_multiplier(rarity)
            adjusted = base_weight * mult
            weighted_list.append((fish_info, adjusted))
            total_weight += adjusted
        
        # 随机选择
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for fish_info, adj_weight in weighted_list:
            cumulative += adj_weight
            if rand <= cumulative:
                return fish_info
        
        # 默认返回第一种
        return weighted_list[0][0]
    
    def _calculate_fish_weight(self, fish_info):
        """计算鱼的重量（在范围内随机）"""
        _, _, min_weight, max_weight, _, _ = fish_info
        return round(random.uniform(min_weight, max_weight), 2)
    
    def _calculate_wait_time(self, fish_info):
        """计算等待时间（根据鱼的稀有度）"""
        _, _, _, _, _, time_range = fish_info
        min_time, max_time = time_range
        base_time = random.uniform(min_time, max_time)
        return base_time * self.game_state.get_wait_time_multiplier()

    def _generate_qte_sequence(self, rarity: str):
        """根据稀有度生成按键序列"""
        pool = ['a', 'd', 'w', 's', 'space']
        length_map = {
            RARITY_COMMON: 1,
            RARITY_UNCOMMON: 2,
            RARITY_RARE: 3,
            RARITY_EPIC: 4
        }
        length = length_map.get(rarity, 1)
        seq = [random.choice(pool[:-1]) for _ in range(length - 1)] if length > 1 else []
        seq.append('space')
        return seq
    
    def set_callbacks(self, on_bite, on_fishing_end):
        """设置回调函数"""
        self.on_bite_callback = on_bite
        self.on_fishing_end_callback = on_fishing_end
    
    def start_fishing(self):
        """开始钓鱼（在新线程中执行）"""
        if self.game_state.is_fishing:
            return False
        
        self.game_state.start_fishing()
        self.game_state.roll_environment()
        self.current_bait_used = self.game_state.consume_bait()
        self.catch_window = self.game_state.get_catch_window()
        
        # 根据当前地点选择要钓的鱼
        location = self.game_state.current_location
        self.current_selected_fish = self._select_fish_by_probability(location)
        
        # 在后台线程中等待随机时间
        self.fishing_thread = threading.Thread(target=self._wait_for_bite, daemon=True)
        self.fishing_thread.start()
        return True
    
    def _wait_for_bite(self):
        """等待咬钩（在后台线程中运行）"""
        if not self.current_selected_fish:
            return
        
        # 根据选中的鱼计算等待时间
        wait_time = self._calculate_wait_time(self.current_selected_fish)
        time.sleep(wait_time)
        
        # 检查是否仍在钓鱼状态
        if not self.game_state.is_fishing:
            return
        
        # 触发咬钩事件
        self.game_state.on_bite()
        rarity = self.current_selected_fish[1]
        self.qte_sequence = self._generate_qte_sequence(rarity)
        self.qte_deadline = time.time() + self.catch_window
        
        # 在主线程中调用UI更新
        if self.on_bite_callback:
            self.root.after(0, lambda seq=self.qte_sequence: self.on_bite_callback(seq))
        
        # 启动反应时间窗口
        catch_thread = threading.Thread(target=self._catch_window_timer, daemon=True)
        catch_thread.start()
    
    def _catch_window_timer(self):
        """反应时间窗口计时器"""
        time.sleep(self.catch_window)
        
        # 如果超时仍未成功，判定为失败
        # 注意：需要再次检查状态，因为用户可能在此期间成功捕获
        if self.game_state.is_bite_occurred and not self.game_state.catch_success:
            self.game_state.on_catch_failed()
            if self.on_fishing_end_callback:
                self.root.after(0, lambda: self.on_fishing_end_callback(False))
    
    def resolve_qte_success(self):
        """QTE 成功，判定钓鱼成功"""
        if self.game_state.is_bite_occurred and not self.game_state.catch_success:
            if not self.current_selected_fish:
                return False
            fish_name = self.current_selected_fish[0]
            rarity = self.current_selected_fish[1]
            min_weight = self.current_selected_fish[2]
            max_weight = self.current_selected_fish[3]
            weight = self._calculate_fish_weight(self.current_selected_fish)
            self.game_state.on_catch_success(fish_name, weight)
            self.game_state.add_caught_fish(fish_name, weight, rarity)
            
            # 计算并添加经验
            exp_gain = self.game_state.calculate_exp_gain(rarity, weight, min_weight, max_weight)
            level_result = self.game_state.add_exp(exp_gain)
            
            if self.on_fishing_end_callback:
                self.root.after(0, lambda: self.on_fishing_end_callback(
                    True, fish_name, weight, exp_gain, level_result
                ))
            return True
        return False
    
    def cancel_fishing(self):
        """取消钓鱼"""
        if self.game_state.is_fishing:
            self.game_state.reset_fishing_state()
            return True
        return False


# ==========================
# 自定义按钮样式
# ==========================
class ModernButton(ttk.Button):
    """现代化按钮样式"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="Modern.TButton", **kwargs)


class StyledLabelFrame(ttk.LabelFrame):
    """自定义标签框架样式"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)


# ==========================
# 场景管理器
# ==========================
class SceneManager:
    """场景管理器，负责切换不同场景"""
    def __init__(self, root, game_state: GameState):
        self.root = root
        self.game_state = game_state
        self.current_scene = None
        self.scenes = {}
        self.main_container = None
        self.top_bar = None  # 顶部状态栏
        self.day_label = None  # 天数标签
        
    def register_scene(self, name: str, scene_class):
        """注册场景"""
        self.scenes[name] = scene_class
        
    def switch_scene(self, scene_name: str, **kwargs):
        """切换场景"""
        if scene_name not in self.scenes:
            print(f"错误：场景 '{scene_name}' 不存在")
            return
        
        # 销毁当前场景
        if self.current_scene:
            self.current_scene.destroy()
            self.current_scene = None
        
        # 确保顶部状态栏存在
        if self.top_bar is None:
            self.top_bar = ttk.Frame(self.root, padding="10 5")
            self.top_bar.pack(fill="x", side="top")
            self.top_bar.configure(relief="solid", borderwidth=1)
            
            # 天数显示
            self.day_label = tk.Label(
                self.top_bar,
                text=f"第 {self.game_state.get_day()} 天",
                font=("Microsoft YaHei", 12, "bold"),
                fg="#FF6B35",
                bg="#F5F5F5"
            )
            self.day_label.pack(side="right", padx=10)
        else:
            # 更新天数显示
            self._update_day_display()
        
        # 确保主容器存在
        if self.main_container is None:
            self.main_container = ttk.Frame(self.root, padding="15")
            self.main_container.pack(fill="both", expand=True)
        
        # 创建新场景
        scene_class = self.scenes[scene_name]
        self.current_scene = scene_class(self.main_container, self.game_state, self, **kwargs)
        self.current_scene.create()
    
    def _update_day_display(self):
        """更新天数显示"""
        if self.day_label:
            self.day_label.config(text=f"第 {self.game_state.get_day()} 天")
        
    def setup_theme(self):
        """设置主题样式（全局）"""
        s = ttk.Style()
        try:
            s.theme_use("xpnative")
        except Exception:
            pass
        
        s.configure(
            "Modern.TButton",
            font=("Microsoft YaHei", 10, "bold"),
            padding=(20, 8)
        )
        s.configure(
            "Styled.TLabelframe",
            font=("Microsoft YaHei", 9, "bold")
        )


# ==========================
# 场景基类
# ==========================
class BaseScene:
    """场景基类"""
    def __init__(self, parent, game_state: GameState, scene_manager: SceneManager):
        self.parent = parent
        self.game_state = game_state
        self.scene_manager = scene_manager
        self.frame = None
        
    def create(self):
        """创建场景界面（子类需实现）"""
        raise NotImplementedError
        
    def destroy(self):
        """销毁场景"""
        if self.frame:
            self.frame.destroy()


# ==========================
# 家场景
# ==========================
class HomeScene(BaseScene):
    """家场景界面"""
    
    def create(self):
        """创建家场景界面"""
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # 标题
        title_label = tk.Label(
            self.frame,
            text="🏠 家",
            font=("Microsoft YaHei", 20, "bold"),
            fg="#4CAAB9",
            bg="#F5F5F5"
        )
        title_label.pack(pady=(0, 20))

        info_top_frame = ttk.Frame(self.frame)
        info_top_frame.pack(fill="x", pady=(0, 8))
        money_label = ttk.Label(info_top_frame, text=f"当前金币：{self.game_state.get_money():.0f}", font=("Microsoft YaHei", 10, "bold"))
        money_label.pack(side="left", padx=(0, 20))
        level = self.game_state.get_level()
        exp = self.game_state.get_exp()
        exp_needed = self.game_state.get_exp_for_next_level()
        if exp_needed > 0:
            level_text = f"等级 {level} | 经验 {exp}/{exp_needed}"
        else:
            level_text = f"等级 {level} (满级)"
        level_label = ttk.Label(info_top_frame, text=level_text, font=("Microsoft YaHei", 10, "bold"), foreground="#FF6B35")
        level_label.pack(side="left")
        
        # 功能区域
        # 1. 睡觉功能
        sleep_frame = StyledLabelFrame(self.frame, text="😴 休息", padding="10")
        sleep_frame.pack(fill="x", pady=(0, 10))
        
        ModernButton(
            sleep_frame,
            text="睡觉",
            command=self._sleep
        ).pack(side="left", padx=5)

        # 1.5 集市
        market_frame = StyledLabelFrame(self.frame, text="🛒 集市", padding="10")
        market_frame.pack(fill="x", pady=(0, 10))
        ModernButton(
            market_frame,
            text="卖鱼/买鱼饵礼物",
            command=lambda: self.scene_manager.switch_scene("market")
        ).pack(side="left", padx=5)
        
        # 2. 家园信息（留空）
        home_info_frame = StyledLabelFrame(self.frame, text="🏡 家园信息", padding="10")
        home_info_frame.pack(fill="x", pady=(0, 10))
        
        info_label = tk.Label(
            home_info_frame,
            text="（预留：后续添加家园信息）",
            font=("Microsoft YaHei", 9),
            bg="#F5F5F5",
            fg="#888888"
        )
        info_label.pack(pady=10)
        
        # 3. 数据图鉴
        data_frame = StyledLabelFrame(self.frame, text="📚 数据图鉴", padding="10")
        data_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        ModernButton(
            data_frame,
            text="查看数据图鉴",
            command=lambda: self.scene_manager.switch_scene("data_book")
        ).pack(side="left", padx=5)
        
        # 4. 钓鱼地点
        fishing_locations_frame = StyledLabelFrame(self.frame, text="🎣 钓鱼地点", padding="10")
        fishing_locations_frame.pack(fill="x", pady=(0, 10))
        
        locations = [
            ("家旁的小溪", "小溪"),
            ("村边河流", "河流"),
            ("附近的湖泊", "湖泊")
        ]
        
        location_frame = ttk.Frame(fishing_locations_frame)
        location_frame.pack(fill="x")
        
        current_level = self.game_state.get_level()
        for i, (display_name, location_id) in enumerate(locations):
            is_unlocked = self.game_state.is_location_unlocked(location_id)
            required_level = LOCATION_UNLOCK_LEVEL.get(location_id, 1)
            
            # 根据是否解锁显示不同的按钮文本和状态
            if is_unlocked:
                btn_text = display_name
                btn_state = "normal"
            else:
                btn_text = f"{display_name} (需要等级{required_level})"
                btn_state = "disabled"
            
            btn = ModernButton(
                location_frame,
                text=btn_text,
                command=lambda loc_id=location_id: self._go_fishing(loc_id),
                state=btn_state
            )
            btn.pack(side="left", padx=5)
        
        # 5. 事件地点（留空）
        events_frame = StyledLabelFrame(self.frame, text="📍 事件地点", padding="10")
        events_frame.pack(fill="x", pady=(0, 10))
        student_state = self.game_state.student_state
        if student_state.get('met'):
            status = "已发现求救，去看看林汐的状况。"
        else:
            status = "暂未发现事件，去河流或湖泊多钓鱼试试。"
        tk.Label(
            events_frame,
            text=status,
            font=("Microsoft YaHei", 9),
            bg="#F5F5F5",
            fg="#666666"
        ).pack(anchor="w", pady=(0, 8))
        ModernButton(
            events_frame,
            text="前往林汐的浅滩",
            state="normal" if student_state.get('met') else "disabled",
            command=lambda: self.scene_manager.switch_scene("student")
        ).pack(side="left", padx=5)
    
    def _sleep(self):
        """睡觉功能"""
        new_day = self.game_state.add_day(1)
        # 更新天数显示
        if self.scene_manager and self.scene_manager.day_label:
            self.scene_manager._update_day_display()
        messagebox.showinfo("睡觉", f"💤 你美美地睡了一觉，精力恢复了！\n新的一天开始了，今天是第 {new_day} 天。")
    
    def _go_fishing(self, location: str):
        """前往钓鱼地点"""
        # 检查等级限制
        if not self.game_state.is_location_unlocked(location):
            required_level = LOCATION_UNLOCK_LEVEL.get(location, 1)
            current_level = self.game_state.get_level()
            messagebox.showwarning(
                "地点未解锁",
                f"需要等级 {required_level} 才能前往 {location}。\n当前等级：{current_level}\n继续钓鱼提升等级吧！"
            )
            return
        self.game_state.current_location = location
        self.scene_manager.switch_scene("fishing", location=location)


# ==========================
# 数据图鉴场景
# ==========================
class DataBookScene(BaseScene):
    """数据图鉴场景"""
    
    def create(self):
        """创建数据图鉴界面"""
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # 标题
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="📚 数据图鉴",
            font=("Microsoft YaHei", 20, "bold"),
            fg="#4CAAB9",
            bg="#F5F5F5"
        )
        title_label.pack(side="left")
        
        # 返回按钮
        ModernButton(
            title_frame,
            text="返回家中",
            command=lambda: self.scene_manager.switch_scene("home")
        ).pack(side="right")
        
        # 统计信息显示
        stats_frame = StyledLabelFrame(self.frame, text="📊 鱼类统计", padding="15")
        stats_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建表格容器
        table_container = ttk.Frame(stats_frame)
        table_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 定义列宽（像素宽度，确保精确对齐）
        col_widths = [50, 140, 100, 100, 120]  # 序号、鱼名、稀有度、捕获数量、最高重量
        
        # 创建表格标题
        header_frame = ttk.Frame(table_container)
        header_frame.pack(fill="x", pady=(0, 0))
        
        # 表头样式
        header_style = {
            'font': ("Microsoft YaHei", 10, "bold"),
            'bg': "#E8E8E8",
            'relief': "solid",
            'bd': 1
        }
        
        # 创建表头（使用固定宽度，居中对齐）
        tk.Label(header_frame, text="序号", width=8, anchor="center", **header_style).grid(row=0, column=0, padx=(0, 1), pady=1, sticky="ew")
        tk.Label(header_frame, text="鱼名", width=20, anchor="center", **header_style).grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        tk.Label(header_frame, text="稀有度", width=14, anchor="center", **header_style).grid(row=0, column=2, padx=1, pady=1, sticky="ew")
        tk.Label(header_frame, text="捕获数量", width=14, anchor="center", **header_style).grid(row=0, column=3, padx=1, pady=1, sticky="ew")
        tk.Label(header_frame, text="最高重量(kg)", width=16, anchor="center", **header_style).grid(row=0, column=4, padx=(1, 0), pady=1, sticky="ew")
        
        # 配置表头列权重
        header_frame.columnconfigure(0, weight=0, minsize=col_widths[0])
        header_frame.columnconfigure(1, weight=1, minsize=col_widths[1])
        header_frame.columnconfigure(2, weight=0, minsize=col_widths[2])
        header_frame.columnconfigure(3, weight=0, minsize=col_widths[3])
        header_frame.columnconfigure(4, weight=0, minsize=col_widths[4])
        
        # 创建滚动区域
        canvas = tk.Canvas(table_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # 配置滚动区域列宽，与表头完全一致
        scrollable_frame.columnconfigure(0, weight=0, minsize=col_widths[0])
        scrollable_frame.columnconfigure(1, weight=1, minsize=col_widths[1])
        scrollable_frame.columnconfigure(2, weight=0, minsize=col_widths[2])
        scrollable_frame.columnconfigure(3, weight=0, minsize=col_widths[3])
        scrollable_frame.columnconfigure(4, weight=0, minsize=col_widths[4])
        
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # 确保canvas窗口宽度与表头一致
            canvas_width = header_frame.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", update_scroll_region)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定canvas宽度变化，保持与表头对齐
        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
            # 同步表头宽度
            header_frame.update_idletasks()
            header_width = header_frame.winfo_width()
            if header_width > 1 and canvas_width != header_width:
                canvas.itemconfig(canvas_window, width=header_width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # 同步表头宽度变化
        def on_header_configure(event):
            header_width = event.width
            if header_width > 1:
                canvas.itemconfig(canvas_window, width=header_width)
        
        header_frame.bind("<Configure>", on_header_configure)
        
        # 获取所有鱼的配置，用于显示
        all_fish = {}
        for location, fish_list in LOCATION_FISH_CONFIG.items():
            for fish_info in fish_list:
                fish_name, rarity, min_weight, max_weight, _, _ = fish_info
                if fish_name not in all_fish:
                    all_fish[fish_name] = {
                        'rarity': rarity,
                        'min_weight': min_weight,
                        'max_weight': max_weight
                    }
        
        # 按稀有度排序显示（杂鱼~ -> 冬雪莲 -> 稀有 -> 史诗）
        rarity_order = [RARITY_COMMON, RARITY_UNCOMMON, RARITY_RARE, RARITY_EPIC]
        sorted_fish = sorted(all_fish.items(), key=lambda x: (
            rarity_order.index(x[1]['rarity']) if x[1]['rarity'] in rarity_order else 999,
            x[0]
        ))
        
        # 单元格样式（统一对齐方式）
        cell_style_base = {
            'font': ("Microsoft YaHei", 9),
            'relief': "solid",
            'bd': 1,
            'padx': 5
        }
        
        # 稀有度颜色映射
        rarity_colors = {
            RARITY_COMMON: "#F0F0F0",      # 浅灰
            RARITY_UNCOMMON: "#E3F2FD",    # 浅蓝
            RARITY_RARE: "#F3E5F5",        # 浅紫
            RARITY_EPIC: "#FFF3E0"         # 浅橙
        }
        
        # 填充表格数据（使用与表头一致的宽度和对齐方式）
        for idx, (fish_name, fish_info) in enumerate(sorted_fish, 1):
            stats = self.game_state.fish_statistics.get(fish_name, {'count': 0, 'max_weight': 0.0})
            count = stats['count']
            max_weight = stats['max_weight']
            rarity = fish_info['rarity']
            
            # 判断是否已钓到
            is_caught = count > 0
            
            # 行背景色（根据稀有度）
            row_bg = rarity_colors.get(rarity, "#FFFFFF")
            
            # 序号（居中对齐，与表头一致）
            cell_style = {**cell_style_base, 'bg': row_bg, 'anchor': "center"}
            tk.Label(scrollable_frame, text=str(idx), width=8, **cell_style).grid(
                row=idx, column=0, padx=(0, 1), pady=1, sticky="ew"
            )
            
            # 鱼名（左对齐，未钓到显示"？？？"）
            fish_display_name = "？？？" if not is_caught else fish_name
            name_bg = "#D0D0D0" if not is_caught else row_bg
            cell_style = {**cell_style_base, 'bg': name_bg, 'anchor': "w"}
            tk.Label(scrollable_frame, text=fish_display_name, width=20, **cell_style).grid(
                row=idx, column=1, padx=1, pady=1, sticky="ew"
            )
            
            # 稀有度（居中对齐，与表头一致）
            rarity_bg = "#D0D0D0" if not is_caught else row_bg
            cell_style = {**cell_style_base, 'bg': rarity_bg, 'anchor': "center"}
            tk.Label(scrollable_frame, text=rarity, width=14, **cell_style).grid(
                row=idx, column=2, padx=1, pady=1, sticky="ew"
            )
            
            # 捕获数量（居中对齐，与表头一致）
            count_text = str(count) if is_caught else "0"
            cell_style = {**cell_style_base, 'bg': row_bg, 'anchor': "center"}
            tk.Label(scrollable_frame, text=count_text, width=14, **cell_style).grid(
                row=idx, column=3, padx=1, pady=1, sticky="ew"
            )
            
            # 最高重量（居中对齐，与表头一致）
            if is_caught and max_weight > 0:
                weight_text = f"{max_weight:.2f}"
            else:
                weight_text = "-"
            cell_style = {**cell_style_base, 'bg': row_bg, 'anchor': "center"}
            tk.Label(scrollable_frame, text=weight_text, width=16, **cell_style).grid(
                row=idx, column=4, padx=(1, 0), pady=1, sticky="ew"
            )
        
        # 配置列权重
        scrollable_frame.columnconfigure(0, weight=0)
        scrollable_frame.columnconfigure(1, weight=1)
        scrollable_frame.columnconfigure(2, weight=0)
        scrollable_frame.columnconfigure(3, weight=0)
        scrollable_frame.columnconfigure(4, weight=0)
        
        # 打包滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 前往钓鱼按钮
        ModernButton(
            self.frame,
            text="前往钓鱼",
            command=lambda: self.scene_manager.switch_scene("fishing")
        ).pack(pady=10)


# ==========================
# 商店与集市场景
# ==========================
class MarketScene(BaseScene):
    """卖鱼与购买道具"""

    def create(self):
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill="x", pady=(0, 12))
        tk.Label(
            title_frame,
            text="🛒 小镇集市",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#4CAAB9",
            bg="#F5F5F5"
        ).pack(side="left")

        ModernButton(
            title_frame,
            text="返回家中",
            command=lambda: self.scene_manager.switch_scene("home")
        ).pack(side="right")

        self.money_var = tk.StringVar()
        ttk.Label(self.frame, textvariable=self.money_var, font=("Microsoft YaHei", 11, "bold"), foreground="#4CAAB9").pack(anchor="w", pady=(0, 8))

        sell_frame = StyledLabelFrame(self.frame, text="💰 卖鱼换钱", padding="10")
        sell_frame.pack(fill="x", pady=(0, 10))
        self.sell_info_var = tk.StringVar()
        ttk.Label(sell_frame, textvariable=self.sell_info_var).pack(anchor="w")
        ModernButton(sell_frame, text="全部卖出", command=self._sell_all).pack(side="left", pady=4)

        bait_frame = StyledLabelFrame(self.frame, text="🎣 鱼饵", padding="10")
        bait_frame.pack(fill="x", pady=(0, 10))
        self._build_buy_buttons(bait_frame, BAIT_CONFIG, category="bait")

        rod_frame = StyledLabelFrame(self.frame, text="🪝 鱼竿 (延长QTE判定时间)", padding="10")
        rod_frame.pack(fill="x", pady=(0, 10))
        self._build_buy_buttons(rod_frame, ROD_CONFIG, category="rod", show_owned=True)

        gift_frame = StyledLabelFrame(self.frame, text="🎁 礼物", padding="10")
        gift_frame.pack(fill="x", pady=(0, 10))
        self._build_buy_buttons(gift_frame, GIFT_SHOP_ITEMS, category="gift")

        craft_frame = StyledLabelFrame(self.frame, text="🍳 烹饪/工具", padding="10")
        craft_frame.pack(fill="x", pady=(0, 10))
        self._build_buy_buttons(craft_frame, CRAFT_ITEMS, category="craft")

        self._refresh()

    def _build_buy_buttons(self, parent, config, category: str, show_owned=False):
        for name, data in config.items():
            price = data.get('price', 0)
            row = ttk.Frame(parent)
            row.pack(fill="x", pady=2)
            extra = ""
            if category == "bait":
                count = self.game_state.inventory['bait_items'].get(name, 0)
                extra = f"（库存 {count}）"
            elif category == "gift":
                count = self.game_state.inventory['gift_items'].get(name, 0)
                extra = f"（库存 {count}）"
            elif category == "craft":
                count = self.game_state.inventory['craft_items'].get(name, 0)
                extra = f"（库存 {count}）"
            elif category == "rod" and show_owned:
                owned = name in self.game_state.get_owned_rods()
                extra = "（已拥有）" if owned else ""
            ttk.Label(row, text=f"{name} - {price} 金 {extra}").pack(side="left")
            ModernButton(row, text="购买", command=lambda n=name, c=category: self._buy(n, c)).pack(side="right")

    def _buy(self, name: str, category: str):
        price = 0
        if category == "bait":
            price = BAIT_CONFIG[name]['price']
        elif category == "gift":
            price = GIFT_SHOP_ITEMS[name]['price']
        elif category == "craft":
            price = CRAFT_ITEMS[name]['price']
        elif category == "rod":
            price = ROD_CONFIG[name]['price']
            if name in self.game_state.get_owned_rods():
                messagebox.showinfo("购买", "已经拥有该鱼竿。")
                return
        if not self.game_state.spend_money(price):
            messagebox.showwarning("余额不足", "金币不够，先去卖鱼吧！")
            return
        if category == "bait":
            self.game_state.acquire_item(name, 3 if price > 0 else 0)
        elif category == "gift":
            self.game_state.acquire_item(name, 1)
        elif category == "craft":
            self.game_state.acquire_item(name, 1)
        elif category == "rod":
            self.game_state.add_rod(name)
        messagebox.showinfo("购买成功", f"获得 {name}")
        self._refresh()

    def _sell_all(self):
        earnings, count = self.game_state.sell_all_fish()
        messagebox.showinfo("卖鱼", f"卖出 {count} 条鱼，收入 {earnings:.1f} 金币。")
        self._refresh()

    def _refresh(self):
        self.money_var.set(f"当前金币：{self.game_state.get_money():.0f}")
        summary = self.game_state.fish_bag_summary()
        if summary:
            parts = [f"{name} x{data['count']} (~{data['total_weight']:.2f}kg)" for name, data in summary.items()]
            self.sell_info_var.set("库存：" + "； ".join(parts))
        else:
            self.sell_info_var.set("库存：无鱼可卖")


# ==========================
# 林汐事件场景
# ==========================
class StudentScene(BaseScene):
    """林汐事件与互动"""

    def create(self):
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)

        # 心情衰减与每日委托初始化
        self.game_state.apply_mood_decay()
        self.game_state.ensure_daily_request()

        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            title_frame,
            text="🎒 林汐的临时营地",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#4CAAB9",
            bg="#F5F5F5"
        ).pack(side="left")

        ModernButton(
            title_frame,
            text="返回家中",
            command=lambda: self.scene_manager.switch_scene("home")
        ).pack(side="right")

        self.trust_var = tk.StringVar()
        self.food_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.request_var = tk.StringVar()
        self.decay_var = tk.StringVar()
        self.gift_choice_var = tk.StringVar()

        info_frame = StyledLabelFrame(self.frame, text="📖 事件概况", padding="12")
        info_frame.pack(fill="x", pady=(0, 12))

        tk.Label(
            info_frame,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 10),
            bg="#F5F5F5",
            justify="left",
            wraplength=560
        ).pack(anchor="w")

        ttk.Label(info_frame, textvariable=self.request_var, foreground="#4CAAB9").pack(anchor="w", pady=(6, 0))
        ttk.Label(info_frame, textvariable=self.decay_var, foreground="#CC6600").pack(anchor="w", pady=(2, 0))

        progress_frame = StyledLabelFrame(self.frame, text="📊 进度", padding="12")
        progress_frame.pack(fill="x", pady=(0, 12))

        # 信任条
        ttk.Label(progress_frame, text="信任度").pack(anchor="w")
        self.trust_bar = ttk.Progressbar(progress_frame, maximum=100, length=520)
        self.trust_bar.pack(anchor="w", pady=4)
        ttk.Label(progress_frame, textvariable=self.trust_var, foreground="#4CAAB9").pack(anchor="w")

        # 补给条
        ttk.Label(progress_frame, text="补给累计 (目标 8kg)" ).pack(anchor="w", pady=(10, 0))
        self.food_bar = ttk.Progressbar(progress_frame, maximum=8.0, length=520)
        self.food_bar.pack(anchor="w", pady=4)
        ttk.Label(progress_frame, textvariable=self.food_var, foreground="#4CAAB9").pack(anchor="w")

        action_frame = StyledLabelFrame(self.frame, text="🤝 互动", padding="12")
        action_frame.pack(fill="x", pady=(0, 12))

        ModernButton(
            action_frame,
            text="聊聊近况（信任+3）",
            command=self._talk
        ).pack(side="left", padx=6)

        ModernButton(
            action_frame,
            text="安排救援返航",
            command=self._try_rescue
        ).pack(side="left", padx=6)

        gift_frame = StyledLabelFrame(self.frame, text="🎁 赠送/烹饪", padding="12")
        gift_frame.pack(fill="x", pady=(0, 12))

        ttk.Label(gift_frame, text="可赠送物品：").pack(side="left")
        self.gift_combo = ttk.Combobox(gift_frame, textvariable=self.gift_choice_var, width=40, state="readonly")
        self.gift_combo.pack(side="left", padx=6)
        self.gift_button = ModernButton(gift_frame, text="赠送", command=self._gift)
        self.gift_button.pack(side="left", padx=4)
        ModernButton(gift_frame, text="简易烹饪（消耗1条鱼）", command=self._cook).pack(side="left", padx=4)

        self._refresh()

    def _refresh(self):
        state = self.game_state.student_state
        name = state.get('name', '林汐')
        trust = state.get('trust', 0)
        food = state.get('food_stock', 0.0)
        rescued = state.get('rescued', False)
        met = state.get('met', False)

        if not met:
            self.status_var.set("你尚未遇见任何求救信号。去河流或湖泊多钓几次吧！")
        elif not rescued:
            self.status_var.set(
                f"{name} 在浅滩等待，你已向她送去 {food:.2f} kg 的鱼肉。信任越高，救援越顺利。"
            )
        else:
            self.status_var.set(
                f"{name} 已被安全送回。她现在会陪你钓鱼，缩短上钩等待时间。"
            )

        self.trust_var.set(f"当前信任度：{trust} / 100")
        self.food_var.set(f"补给：{food:.2f} / 8.00 kg")
        self.trust_bar['value'] = trust
        self.food_bar['value'] = min(8.0, food)
        daily = state.get('daily_request')
        if daily:
            desc = daily.get('desc', '')
            self.request_var.set(f"今日委托：{desc}")
        else:
            self.request_var.set("今日委托：暂无")
        # 每日赠送限制提示和按钮状态
        current_day = self.game_state.get_day()
        last_gift_day = state.get('last_gift_day', 0)
        if last_gift_day >= current_day:
            gift_status = f"今日已赠送（每天只能送一次）"
            if hasattr(self, 'gift_button'):
                self.gift_button.config(state="disabled")
        else:
            gift_status = "今日未赠送"
            if hasattr(self, 'gift_button'):
                self.gift_button.config(state="normal")
        self.decay_var.set(f"赠送状态：{gift_status}")

        # 赠送选项
        options = self._build_gift_options()
        self.gift_options = options
        if options:
            self.gift_combo['values'] = [opt['display'] for opt in options]
            self.gift_combo.current(0)
        else:
            self.gift_combo['values'] = ["（背包无可赠送物品）"]
            self.gift_combo.current(0)

    def _talk(self):
        gained = self.game_state.boost_student_trust()
        if gained > 0:
            messagebox.showinfo("对话", f"你们聊了聊校园趣事，信任+{gained}")
        else:
            messagebox.showinfo("对话", "还未遇见林汐，先去钓鱼看看吧。")
        self._refresh()

    def _try_rescue(self):
        if self.game_state.try_rescue_student():
            messagebox.showinfo(
                "救援成功",
                "你把补给和绳索送达，林汐安全返回！\n她决定留下来帮忙，钓鱼等待时间将缩短。"
            )
        else:
            messagebox.showwarning(
                "条件不足",
                "补给未达 8kg，或尚未遇见求救信号。继续钓鱼积累补给吧！"
            )
        self._refresh()

    def _build_gift_options(self):
        options = []
        # 鱼类
        for fish in self.game_state.fish_bag_summary().items():
            name, data = fish
            count = data['count']
            avg_weight = data['total_weight'] / max(1, count)
            options.append({
                'display': f"鱼 x{count} | {name} (~{avg_weight:.2f}kg)",
                'type': 'fish',
                'name': name,
                'weight': avg_weight
            })
        # 料理
        cooked = self.game_state.inventory.get('cooked_items', {})
        if cooked.get('烤鱼', 0) > 0:
            options.append({
                'display': f"烤鱼 x{cooked['烤鱼']} (热食)",
                'type': 'cooked',
                'name': '烤鱼',
                'weight': 0.8,
                'tags': ['热食', '鱼肉']
            })
        # 礼物
        for name, count in self.game_state.inventory.get('gift_items', {}).items():
            if count > 0:
                options.append({
                    'display': f"礼物 x{count} | {name}",
                    'type': 'gift',
                    'name': name,
                    'tags': GIFT_SHOP_ITEMS.get(name, {}).get('tags', [])
                })
        return options

    def _gift(self):
        if not hasattr(self, 'gift_options') or not self.gift_options:
            messagebox.showinfo("赠送", "背包里没有可赠送的物品。")
            return
        idx = self.gift_combo.current()
        if idx < 0 or idx >= len(self.gift_options):
            return
        opt = self.gift_options[idx]
        
        # 先检查今天是否已经送过
        current_day = self.game_state.get_day()
        last_gift_day = self.game_state.student_state.get('last_gift_day', 0)
        if last_gift_day >= current_day:
            messagebox.showwarning("赠送", "今天已经送过礼物了，明天再来吧！")
            return
        
        if opt['type'] == 'fish':
            fish = self.game_state.remove_one_fish(opt['name'])
            if not fish:
                messagebox.showwarning("赠送", "鱼袋里已经没有这种鱼了。")
                self._refresh()
                return
            weight = fish.get('weight', opt.get('weight', 0.5))
            result = self.game_state.gift_to_student(opt['name'], tags=['生鱼', '鱼肉'], weight=weight)
            if not result.get('success', True):
                messagebox.showwarning("赠送", result.get('note', '赠送失败'))
                self._refresh()
                return
            message = f"送出 {opt['name']}，信任变化 {result['trust_delta']}，累计补给 {result['food_stock']:.2f} kg"
            messagebox.showinfo("赠送成功", message)
        elif opt['type'] == 'cooked':
            if not self.game_state.consume_item(opt['name']):
                messagebox.showwarning("赠送", "没有烤鱼可送。")
                self._refresh()
                return
            result = self.game_state.gift_to_student(opt['name'], tags=opt.get('tags', []), weight=1.0)
            if not result.get('success', True):
                messagebox.showwarning("赠送", result.get('note', '赠送失败'))
                self._refresh()
                return
            messagebox.showinfo("赠送成功", f"送出热乎的烤鱼，信任变化 {result['trust_delta']}")
        else:
            if not self.game_state.consume_item(opt['name']):
                messagebox.showwarning("赠送", "礼物数量不足。")
                self._refresh()
                return
            result = self.game_state.gift_to_student(opt['name'], tags=opt.get('tags', []), weight=0.0)
            if not result.get('success', True):
                messagebox.showwarning("赠送", result.get('note', '赠送失败'))
                self._refresh()
                return
            messagebox.showinfo("赠送成功", f"送出 {opt['name']}，信任变化 {result['trust_delta']}")
        self._refresh()

    def _cook(self):
        ok, msg = self.game_state.cook_one_fish()
        if ok:
            messagebox.showinfo("烹饪", msg)
        else:
            messagebox.showwarning("烹饪", msg)
        self._refresh()


# ==========================
# 钓鱼场景
# ==========================
class FishingScene(BaseScene):
    """钓鱼场景界面"""
    
    def __init__(self, parent, game_state: GameState, scene_manager: SceneManager, location="默认地点"):
        super().__init__(parent, game_state, scene_manager)
        self.location = location
        self._failure_popup_shown = False  # 标志：是否已显示失败弹窗
        
    def create(self):
        """创建钓鱼场景界面"""
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill="both", expand=True)
        
        # 标题和返回按钮
        title_frame = ttk.Frame(self.frame)
        title_frame.pack(fill="x", pady=(0, 15))
        
        location_name = self.location if self.location != "default" else "默认地点"
        title_label = tk.Label(
            title_frame,
            text=f"🎣 钓鱼 - {location_name}",
            font=("Microsoft YaHei", 18, "bold"),
            fg="#4CAAB9",
            bg="#F5F5F5"
        )
        title_label.pack(side="left")
        
        ModernButton(
            title_frame,
            text="返回家中",
            command=lambda: self.scene_manager.switch_scene("home")
        ).pack(side="right")
        
        # 游戏状态
        self.game_state.current_location = self.location
        
        # 钓鱼管理器
        self.fishing_manager = FishingManager(self.game_state, self.scene_manager.root)
        self.fishing_manager.set_callbacks(
            on_bite=self._on_bite,
            on_fishing_end=self._on_fishing_end
        )
        
        # 界面变量
        self.status_var = tk.StringVar(value="🟢 就绪")
        self.info_var = tk.StringVar(value="点击'开始钓鱼'按钮开始游戏")
        self.bite_alert_var = tk.StringVar(value="")
        self.qte_var = tk.StringVar(value="")
        self.environment_var = tk.StringVar(value="")
        self.money_var = tk.StringVar(value=f"金币：{self.game_state.get_money():.0f}")
        self.level_var = tk.StringVar()
        self.qte_sequence = []
        self.qte_index = 0
        self.qte_deadline = None
        self.qte_timer_id = None
        
        # 呼吸灯点相关
        self.breathing_frame = None
        self.breathing_canvas = None
        self.breathing_dots = []  # 存储三个点的ID
        self.breathing_animation_id = None
        self.breathing_phase = 0  # 动画相位
        
        # 绑定键盘
        self.scene_manager.root.bind('<KeyPress>', self._on_key_pressed)
        self.scene_manager.root.focus_set()
        
        # 创建界面组件
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 游戏区域
        game_frame = StyledLabelFrame(self.frame, text="🎮 游戏区域", padding="15")
        game_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 状态显示
        status_label = tk.Label(
            game_frame,
            textvariable=self.status_var,
            font=("Microsoft YaHei", 12),
            bg="#F5F5F5"
        )
        status_label.pack(pady=10)
        
        # 信息显示
        info_label = tk.Label(
            game_frame,
            textvariable=self.info_var,
            font=("Microsoft YaHei", 10),
            bg="#F5F5F5",
            wraplength=500
        )
        info_label.pack(pady=10)

        env_frame = ttk.Frame(game_frame)
        env_frame.pack(fill="x", pady=(0, 6))
        ttk.Label(env_frame, textvariable=self.environment_var).pack(side="left", padx=4)
        ttk.Label(env_frame, textvariable=self.level_var, foreground="#FF6B35", font=("Microsoft YaHei", 10, "bold")).pack(side="right", padx=4)
        ttk.Label(env_frame, textvariable=self.money_var, foreground="#4CAAB9").pack(side="right", padx=4)

        equip_frame = ttk.Frame(game_frame)
        equip_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(equip_frame, text="鱼饵：").pack(side="left")
        self.bait_combo = ttk.Combobox(
            equip_frame,
            values=list(BAIT_CONFIG.keys()),
            state="readonly",
            width=12
        )
        self.bait_combo.set(self.game_state.inventory.get('selected_bait', '普通鱼饵'))
        self.bait_combo.bind("<<ComboboxSelected>>", lambda e: self._on_bait_change())
        self.bait_combo.pack(side="left", padx=4)
        ttk.Label(equip_frame, text="鱼竿：").pack(side="left", padx=(10, 0))
        self.rod_combo = ttk.Combobox(
            equip_frame,
            values=self.game_state.get_owned_rods(),
            state="readonly",
            width=12
        )
        self.rod_combo.set(self.game_state.inventory.get('equipped_rod', '木质竿'))
        self.rod_combo.bind("<<ComboboxSelected>>", lambda e: self._on_rod_change())
        self.rod_combo.pack(side="left", padx=4)
        ttk.Label(equip_frame, text="(高级鱼竿延长QTE时间)").pack(side="left", padx=6)
        
        # 呼吸灯点区域（钓鱼时显示）
        self.breathing_frame = ttk.Frame(game_frame)
        self.breathing_canvas = tk.Canvas(
            self.breathing_frame,
            width=120,
            height=30,
            bg="#F5F5F5",
            highlightthickness=0
        )
        self.breathing_canvas.pack()
        
        # 创建三个点（初始隐藏）
        dot_radius = 8
        spacing = 30
        start_x = 30
        y = 15
        
        for i in range(3):
            x = start_x + i * spacing
            dot_id = self.breathing_canvas.create_oval(
                x - dot_radius, y - dot_radius,
                x + dot_radius, y + dot_radius,
                fill="#CCCCCC",  # 初始浅灰色
                outline=""
            )
            self.breathing_dots.append(dot_id)
        
        # 咬钩提示（大字体，醒目）
        bite_alert_label = tk.Label(
            game_frame,
            textvariable=self.bite_alert_var,
            font=("Microsoft YaHei", 24, "bold"),
            fg="#FF0000",
            bg="#F5F5F5"
        )
        bite_alert_label.pack(pady=20)

        qte_label = tk.Label(
            game_frame,
            textvariable=self.qte_var,
            font=("Consolas", 12, "bold"),
            fg="#444444",
            bg="#F5F5F5"
        )
        qte_label.pack(pady=(0, 10))
        
        # 操作按钮区域
        button_frame = ttk.Frame(game_frame)
        button_frame.pack(pady=20)
        
        self.fishing_button = ModernButton(
            button_frame,
            text="开始钓鱼",
            command=self._start_fishing
        )
        self.fishing_button.pack(side="left", padx=10)
        
        self.cancel_button = ModernButton(
            button_frame,
            text="取消钓鱼",
            command=self._cancel_fishing,
            state="disabled"
        )
        self.cancel_button.pack(side="left", padx=10)
        
        # 底部状态栏
        status_bar = ttk.Frame(self.frame)
        status_bar.pack(fill="x", side="bottom")
        
        ttk.Label(
            status_bar,
            text="提示: 咬钩后按提示键完成QTE (最后一键总是空格)。",
            anchor="w"
        ).pack(fill="x", padx=8, pady=4)
        
        # 初始化等级显示
        self._refresh_level_display()
    
    def _start_breathing(self):
        """开始呼吸灯动画"""
        self.breathing_frame.pack(pady=10)
        self.breathing_phase = 0
        self._animate_breathing()
    
    def _stop_breathing(self):
        """停止呼吸灯动画"""
        if self.breathing_animation_id:
            self.scene_manager.root.after_cancel(self.breathing_animation_id)
            self.breathing_animation_id = None
        self.breathing_frame.pack_forget()
        self.breathing_phase = 0
        # 重置所有点为浅色
        for dot_id in self.breathing_dots:
            self.breathing_canvas.itemconfig(dot_id, fill="#CCCCCC")
    
    def _animate_breathing(self):
        """呼吸灯动画 - 三个点循环呼吸效果"""
        if not (self.game_state.is_fishing and self.game_state.is_waiting_for_bite):
            self._stop_breathing()
            return
        
        num_dots = len(self.breathing_dots)
        
        # 计算每个点的亮度
        # 使用正弦波，三个点相位差120度，形成循环呼吸效果
        for i, dot_id in enumerate(self.breathing_dots):
            # 每个点相位差 2π/3 (120度)
            phase = (self.breathing_phase + i * 2 * 3.14159 / num_dots) % (2 * 3.14159)
            # 使用正弦函数计算亮度，范围在0.3-1.0之间
            brightness = 0.65 + 0.35 * (1 + 0.7 * (1 - abs(phase - 3.14159) / 3.14159)) / 2
            brightness = max(0.3, min(1.0, brightness))
            
            # 将亮度转换为颜色（深色=亮，浅色=暗）
            # 亮度高时颜色深（#666666），亮度低时颜色浅（#CCCCCC）
            gray_value = int(204 - (204 - 102) * brightness)
            color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
            
            self.breathing_canvas.itemconfig(dot_id, fill=color)
        
        # 更新相位（每帧增加0.15，约12帧完成一个周期）
        self.breathing_phase += 0.15
        if self.breathing_phase >= 2 * 3.14159:
            self.breathing_phase = 0
        
        # 继续动画（每100ms更新一次，形成流畅的呼吸效果）
        self.breathing_animation_id = self.scene_manager.root.after(100, self._animate_breathing)
    
    def _start_fishing(self):
        """开始钓鱼"""
        if self.fishing_manager.start_fishing():
            self.status_var.set("🎣 钓鱼中...")
            self.info_var.set("等待鱼儿上钩... 天气与时间会影响上钩速度和稀有度。")
            self.bite_alert_var.set("")
            self.qte_var.set("")
            self.fishing_button.config(state="disabled")
            self.cancel_button.config(state="normal")
            self._start_breathing()
            self._refresh_environment_display()
            self._refresh_money_display()
            self._refresh_level_display()
            self.scene_manager.root.focus_set()
            # 开始新的钓鱼时重置失败弹窗标志
            self._failure_popup_shown = False
    
    def _cancel_fishing(self):
        """取消钓鱼"""
        if self.fishing_manager.cancel_fishing():
            self.status_var.set("🟢 就绪")
            self.info_var.set("已取消钓鱼")
            self.bite_alert_var.set("")
            self.qte_var.set("")
            self._stop_breathing()
            self.fishing_button.config(state="normal")
            self.cancel_button.config(state="disabled")
    
    def _on_bite(self, sequence):
        """咬钩事件处理"""
        self.qte_sequence = sequence or []
        self.qte_index = 0
        self.qte_deadline = time.time() + self.fishing_manager.catch_window
        self._stop_breathing()
        self.status_var.set("⚡ 上钩了！")
        self.info_var.set("按提示键完成QTE，最后一键一定是空格！")
        self.bite_alert_var.set("上钩！")
        self._update_qte_label()
    
    def _on_fishing_end(self, success: bool, fish_name: str = None, weight: float = None, 
                        exp_gain: int = 0, level_result: dict = None):
        """钓鱼结束事件处理"""
        self._stop_breathing()
        self.qte_var.set("")
        if success and fish_name and weight:
            self.status_var.set("✅ 成功钓到鱼！")
            # 构建信息字符串
            info_parts = [f"恭喜！你成功捕获了 {fish_name}（{weight}kg）！"]
            if exp_gain > 0:
                info_parts.append(f"获得经验 +{exp_gain}")
            elif level_result and level_result.get('note'):
                # 如果今天已升级，显示提示信息
                info_parts.append(level_result.get('note', ''))
            self.info_var.set(" | ".join(info_parts))
            
            # 构建消息框内容
            msg_parts = [f"🎉 成功钓到 {fish_name}！\n重量：{weight}kg"]
            if exp_gain > 0:
                msg_parts.append(f"\n获得经验：+{exp_gain}")
                current_exp = self.game_state.get_exp()
                exp_needed = self.game_state.get_exp_for_next_level()
                if exp_needed > 0:
                    msg_parts.append(f"\n当前经验：{current_exp}/{exp_needed}")
            elif level_result and level_result.get('note'):
                # 如果今天已升级，显示提示信息
                msg_parts.append(f"\n{level_result.get('note', '')}")
            
            # 检查是否升级
            if level_result and level_result.get('leveled_up'):
                new_level = level_result.get('new_level', 1)
                msg_parts.append(f"\n\n✨ 等级提升！当前等级：{new_level}")
                unlocked = level_result.get('unlocked_location')
                if unlocked:
                    msg_parts.append(f"\n🎯 解锁新地点：{unlocked}！")
            
            messagebox.showinfo("成功", "\n".join(msg_parts))
            self._check_student_event(fish_name, weight)
            self._refresh_level_display()
            # 成功后重置失败弹窗标志
            self._failure_popup_shown = False
        else:
            self.status_var.set("❌ 失败")
            self.info_var.set("反应太慢了，鱼儿跑掉了...")
            # 只在第一次失败时显示弹窗
            if not self._failure_popup_shown:
                messagebox.showwarning("失败", "反应太慢了，鱼儿跑掉了！")
                self._failure_popup_shown = True
        
        # 重置界面
        self.bite_alert_var.set("")
        self.fishing_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
        # 重置游戏状态
        self.game_state.reset_fishing_state()

    def _on_key_pressed(self, event):
        """键盘按下事件处理，用于QTE"""
        if not self.game_state.is_bite_occurred:
            return
        if not self.qte_sequence:
            return
        key = event.keysym.lower()
        if key == 'space':
            key = 'space'
        if time.time() > (self.qte_deadline or 0):
            self._fail_qte()
            return
        expected = self.qte_sequence[self.qte_index]
        if key == expected:
            self.qte_index += 1
            self._update_qte_label()
            if self.qte_index >= len(self.qte_sequence):
                self.fishing_manager.resolve_qte_success()
        else:
            self._fail_qte()

    def _fail_qte(self):
        self.game_state.on_catch_failed()
        self._on_fishing_end(False)
        self.game_state.reset_fishing_state()
        self.qte_sequence = []
        self.qte_index = 0
        self.qte_deadline = None

    def _update_qte_label(self):
        if not self.qte_sequence:
            self.qte_var.set("")
            return
        parts = []
        for idx, key in enumerate(self.qte_sequence):
            if idx == self.qte_index:
                parts.append(f"[{key.upper()}]")
            else:
                parts.append(key.upper())
        remain = max(0.0, (self.qte_deadline or time.time()) - time.time())
        self.qte_var.set(" -> ".join(parts) + f"    剩余 {remain:.1f}s")

    def _refresh_environment_display(self):
        weather = getattr(self.game_state, 'current_weather', '晴朗')
        slot = getattr(self.game_state, 'current_time_slot', '清晨')
        bait = self.game_state.inventory.get('selected_bait', '普通鱼饵')
        rod = self.game_state.inventory.get('equipped_rod', '木质竿')
        self.environment_var.set(f"天气：{weather}｜时间：{slot}｜鱼饵：{bait}｜鱼竿：{rod}")

    def _refresh_money_display(self):
        self.money_var.set(f"金币：{self.game_state.get_money():.0f}")
    
    def _refresh_level_display(self):
        """刷新等级和经验显示"""
        level = self.game_state.get_level()
        exp = self.game_state.get_exp()
        exp_needed = self.game_state.get_exp_for_next_level()
        if exp_needed > 0:
            self.level_var.set(f"等级 {level} | 经验 {exp}/{exp_needed}")
        else:
            self.level_var.set(f"等级 {level} (满级)")

    def _on_bait_change(self):
        bait = self.bait_combo.get()
        self.game_state.select_bait(bait)
        self._refresh_environment_display()

    def _on_rod_change(self):
        rod = self.rod_combo.get()
        self.game_state.equip_rod(rod)
        self._refresh_environment_display()

    def _check_student_event(self, fish_name: str, weight: float):
        """检查女高中生事件触发与加成"""
        state = self.game_state.student_state
        # 首次遇见：在河流或湖泊捕鱼时概率触发
        if not state.get('met') and self.location in ("河流", "湖泊"):
            state['encounter_rolls'] = state.get('encounter_rolls', 0) + 1
            chance = min(0.6, 0.18 + 0.08 * state['encounter_rolls'])
            if random.random() < chance:
                self.game_state.register_student_encounter()
                messagebox.showinfo(
                    "漂流瓶",
                    "你钓起了一个漂流瓶，里面的字条写着：\n\n我是附近高中的社团实习生林汐，被困在浅滩，请带上食物和绳索来帮忙！\n\n回到家中后，可以在事件里找到她的求救位置。"
                )
                return
        # 已遇见：提示去事件面板赠送或烹饪
        if state.get('met'):
            self.info_var.set("可在事件面板赠送鱼或礼物提升好感，或卖鱼换钱去买喜好物。")
    
    def destroy(self):
        """销毁场景（解绑按键事件）"""
        if self.frame:
            # 解绑空格键（避免影响其他场景）
            self.scene_manager.root.unbind('<KeyPress>')
            self.frame.destroy()


# ==========================
# 游戏UI界面（主界面管理器）
# ==========================
class FishingGameUI:
    APP_NAME = "🎣 钓鱼，然后捡到女高中生"
    
    def __init__(self, root):
        self.root = root
        self.root.title(self.APP_NAME)
        self.root.geometry("960x720")
        self.root.configure(bg="#F5F5F5")
        
        # 游戏状态
        self.game_state = GameState()
        
        # 绑定窗口关闭事件，保存数据
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # 场景管理器
        self.scene_manager = SceneManager(root, self.game_state)
        self.scene_manager.setup_theme()
        
        # 注册场景
        self.scene_manager.register_scene("home", HomeScene)
        self.scene_manager.register_scene("fishing", FishingScene)
        self.scene_manager.register_scene("data_book", DataBookScene)
        self.scene_manager.register_scene("student", StudentScene)
        self.scene_manager.register_scene("market", MarketScene)
        
        # 初始化场景（家场景）
        self.scene_manager.switch_scene("home")
    
    def _on_closing(self):
        """窗口关闭时的处理"""
        # 保存统计数据
        self.game_state.save_stats()
        self.root.destroy()
    


# ==========================
# 主程序入口
# ==========================
def main():
    root = tk.Tk()
    DPIManager.setup(root)
    app = FishingGameUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
