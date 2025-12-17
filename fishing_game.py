"""
钓鱼小游戏
功能：点击钓鱼后开始钓鱼，经过随机时间后弹出"上钩！"提示，
      玩家必须在1秒内按空格键才能成功钓到鱼。
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
# 统计文件管理
# ==========================
STATS_FILE = "fishing_stats.json"

def load_statistics():
    """从文件加载统计数据"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('fish_statistics', {}), data.get('money', 0)
        except Exception as e:
            print(f"加载统计数据失败: {e}")
            return {}, 0
    return {}, 0

def save_statistics(fish_statistics, money=0):
    """保存统计数据到文件"""
    try:
        data = {
            'fish_statistics': fish_statistics,
            'money': money,
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
        self.fish_statistics, self.money = load_statistics()
        
        # 预留扩展字段
        self.current_location = "小溪"  # 当前钓鱼地点（默认小溪）
        self.home_data = {}  # 家园数据（预留）
        
        # 初始化所有鱼的统计数据（如果文件中没有）
        self._init_fish_statistics()
    
    def _init_fish_statistics(self):
        """初始化所有鱼的统计数据"""
        for location, fish_list in LOCATION_FISH_CONFIG.items():
            for fish_name, _, _, _, _, _ in fish_list:
                if fish_name not in self.fish_statistics:
                    self.fish_statistics[fish_name] = {'count': 0, 'max_weight': 0.0}
    
    def save_stats(self):
        """保存统计数据到文件"""
        save_statistics(self.fish_statistics, self.money)
    
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
        
        # 钓鱼参数
        self.catch_window = 1.0  # 咬钩后的反应时间窗口（秒）
        
        # 回调函数（由UI设置）
        self.on_bite_callback = None  # 咬钩时的回调
        self.on_fishing_end_callback = None  # 钓鱼结束时的回调
    
    def _select_fish_by_probability(self, location: str):
        """根据概率选择要钓的鱼"""
        # 如果地点不存在，默认使用小溪
        fish_list = LOCATION_FISH_CONFIG.get(location, LOCATION_FISH_CONFIG["小溪"])
        
        # 计算总权重
        total_weight = sum(weight for _, _, _, _, weight, _ in fish_list)
        
        # 随机选择
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for fish_info in fish_list:
            cumulative += fish_info[4]  # 概率权重
            if rand <= cumulative:
                return fish_info
        
        # 默认返回第一种
        return fish_list[0]
    
    def _calculate_fish_weight(self, fish_info):
        """计算鱼的重量（在范围内随机）"""
        _, _, min_weight, max_weight, _, _ = fish_info
        return round(random.uniform(min_weight, max_weight), 2)
    
    def _calculate_wait_time(self, fish_info):
        """计算等待时间（根据鱼的稀有度）"""
        _, _, _, _, _, time_range = fish_info
        min_time, max_time = time_range
        return random.uniform(min_time, max_time)
    
    def set_callbacks(self, on_bite, on_fishing_end):
        """设置回调函数"""
        self.on_bite_callback = on_bite
        self.on_fishing_end_callback = on_fishing_end
    
    def start_fishing(self):
        """开始钓鱼（在新线程中执行）"""
        if self.game_state.is_fishing:
            return False
        
        self.game_state.start_fishing()
        
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
        
        # 在主线程中调用UI更新
        if self.on_bite_callback:
            self.root.after(0, self.on_bite_callback)
        
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
    
    def try_catch(self):
        """尝试捕获（按下空格键时调用）"""
        if self.game_state.is_bite_occurred and not self.game_state.catch_success:
            if not self.current_selected_fish:
                return False
            
            # 计算鱼的重量
            fish_name = self.current_selected_fish[0]
            weight = self._calculate_fish_weight(self.current_selected_fish)
            
            # 成功钓到鱼
            self.game_state.on_catch_success(fish_name, weight)
            if self.on_fishing_end_callback:
                self.root.after(0, lambda: self.on_fishing_end_callback(True, fish_name, weight))
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
        
        # 确保主容器存在
        if self.main_container is None:
            self.main_container = ttk.Frame(self.root, padding="15")
            self.main_container.pack(fill="both", expand=True)
        
        # 创建新场景
        scene_class = self.scenes[scene_name]
        self.current_scene = scene_class(self.main_container, self.game_state, self, **kwargs)
        self.current_scene.create()
        
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
        
        # 功能区域
        # 1. 睡觉功能
        sleep_frame = StyledLabelFrame(self.frame, text="😴 休息", padding="10")
        sleep_frame.pack(fill="x", pady=(0, 10))
        
        ModernButton(
            sleep_frame,
            text="睡觉",
            command=self._sleep
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
        
        for i, (display_name, location_id) in enumerate(locations):
            btn = ModernButton(
                location_frame,
                text=display_name,
                command=lambda loc_id=location_id: self._go_fishing(loc_id)
            )
            btn.pack(side="left", padx=5)
        
        # 5. 事件地点（留空）
        events_frame = StyledLabelFrame(self.frame, text="📍 事件地点", padding="10")
        events_frame.pack(fill="x", pady=(0, 10))
        
        events_label = tk.Label(
            events_frame,
            text="商店、小镇等（预留：后续添加）",
            font=("Microsoft YaHei", 9),
            bg="#F5F5F5",
            fg="#888888"
        )
        events_label.pack(pady=10)
    
    def _sleep(self):
        """睡觉功能"""
        messagebox.showinfo("睡觉", "💤 你美美地睡了一觉，精力恢复了！")
    
    def _go_fishing(self, location: str):
        """前往钓鱼地点"""
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
# 钓鱼场景
# ==========================
class FishingScene(BaseScene):
    """钓鱼场景界面"""
    
    def __init__(self, parent, game_state: GameState, scene_manager: SceneManager, location="默认地点"):
        super().__init__(parent, game_state, scene_manager)
        self.location = location
        
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
        
        # 呼吸灯点相关
        self.breathing_frame = None
        self.breathing_canvas = None
        self.breathing_dots = []  # 存储三个点的ID
        self.breathing_animation_id = None
        self.breathing_phase = 0  # 动画相位
        
        # 绑定空格键
        self.scene_manager.root.bind('<KeyPress-space>', self._on_space_pressed)
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
            text="提示: 咬钩后按空格键捕获！",
            anchor="w"
        ).pack(fill="x", padx=8, pady=4)
    
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
            self.info_var.set("等待鱼儿上钩...")
            self.bite_alert_var.set("")
            self.fishing_button.config(state="disabled")
            self.cancel_button.config(state="normal")
            self._start_breathing()
            self.scene_manager.root.focus_set()
    
    def _cancel_fishing(self):
        """取消钓鱼"""
        if self.fishing_manager.cancel_fishing():
            self.status_var.set("🟢 就绪")
            self.info_var.set("已取消钓鱼")
            self.bite_alert_var.set("")
            self._stop_breathing()
            self.fishing_button.config(state="normal")
            self.cancel_button.config(state="disabled")
    
    def _on_bite(self):
        """咬钩事件处理"""
        self._stop_breathing()
        self.status_var.set("⚡ 上钩了！")
        self.info_var.set("快速按空格键捕获！")
        self.bite_alert_var.set("上钩！")
    
    def _on_fishing_end(self, success: bool, fish_name: str = None, weight: float = None):
        """钓鱼结束事件处理"""
        self._stop_breathing()
        
        if success and fish_name and weight:
            self.status_var.set("✅ 成功钓到鱼！")
            self.info_var.set(f"恭喜！你成功捕获了 {fish_name}（{weight}kg）！")
            messagebox.showinfo("成功", f"🎉 成功钓到 {fish_name}！\n重量：{weight}kg")
        else:
            self.status_var.set("❌ 失败")
            self.info_var.set("反应太慢了，鱼儿跑掉了...")
            messagebox.showwarning("失败", "反应太慢了，鱼儿跑掉了！")
        
        # 重置界面
        self.bite_alert_var.set("")
        self.fishing_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        
        # 重置游戏状态
        self.game_state.reset_fishing_state()
    
    def _on_space_pressed(self, event):
        """空格键按下事件处理"""
        if self.game_state.is_bite_occurred:
            self.fishing_manager.try_catch()
    
    def destroy(self):
        """销毁场景（解绑按键事件）"""
        if self.frame:
            # 解绑空格键（避免影响其他场景）
            self.scene_manager.root.unbind('<KeyPress-space>')
            self.frame.destroy()


# ==========================
# 游戏UI界面（主界面管理器）
# ==========================
class FishingGameUI:
    APP_NAME = "🎣 钓鱼小游戏"
    
    def __init__(self, root):
        self.root = root
        self.root.title(self.APP_NAME)
        self.root.geometry("700x600")
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
