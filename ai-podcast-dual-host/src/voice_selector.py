# -*- coding: utf-8 -*-
"""
音色选择器
加载完整 TTS 音色列表，为 Persona Extractor 提供动态选择能力
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class VoiceSelector:
    """TTS 音色选择器"""

    def __init__(self, voice_list_path: Optional[Path] = None):
        """
        初始化音色选择器

        Args:
            voice_list_path: 音色列表 JSON 文件路径，默认使用 api/TTS-voice-list.json
        """
        if voice_list_path is None:
            self.voice_list_path = Path(__file__).parent.parent / "api" / "TTS-voice-list.json"
        else:
            self.voice_list_path = voice_list_path

        self._voices: List[Dict] = []
        self._loaded = False

    def load_voices(self) -> List[Dict]:
        """
        加载音色列表

        Returns:
            音色列表
        """
        if self._loaded:
            return self._voices

        try:
            with open(self.voice_list_path, 'r', encoding='utf-8') as f:
                self._voices = json.load(f)
            self._loaded = True
        except Exception as e:
            print(f"[Warning] 加载音色列表失败: {e}")
            self._voices = []

        return self._voices

    def get_voices_by_gender(self, gender: str) -> List[Dict]:
        """
        按性别筛选音色

        Args:
            gender: "male" 或 "female"

        Returns:
            符合条件的音色列表
        """
        voices = self.load_voices()

        if gender not in ["male", "female"]:
            return voices

        result = []
        for v in voices:
            voice_type = v.get("voice_type", "")

            # 根据 voice_type 判断性别
            # female: zh_female_... , male: zh_male_... , en_male_... , en_female_...
            if gender == "female":
                if "_female_" in voice_type or "女" in v.get("音色名称", ""):
                    result.append(v)
            else:  # male
                if "_male_" in voice_type and "_female_" not in voice_type:
                    # 排除像 "zh_male_sophie_uranus_bigtts" 这种历史遗留命名
                    # 但 sophie 实际是女声，需要额外判断
                    name = v.get("音色名称", "")
                    if "女" not in name:  # 确保名称中没有"女"字
                        result.append(v)

        return result

    def build_selection_prompt(self, gender: str = "female", max_voices: int = 15) -> str:
        """
        构建音色选择 prompt，供 Persona Extractor 使用

        Args:
            gender: 性别筛选 ("male" 或 "female")
            max_voices: 最多返回多少条音色（避免 prompt 过长）

        Returns:
            格式化的音色列表文本
        """
        voices = self.get_voices_by_gender(gender)

        if not voices:
            return ""

        lines = []
        lines.append("## 可用 TTS 音色列表")
        lines.append(f"（根据 gender='{gender}' 筛选，共 {len(voices)} 个音色）")
        lines.append("")

        # 按场景分组
        scenes = {}
        for v in voices:
            scene = v.get("场景", "其他")
            if scene not in scenes:
                scenes[scene] = []
            scenes[scene].append(v)

        # 构建输出
        count = 0
        for scene, scene_voices in scenes.items():
            if count >= max_voices:
                break

            lines.append(f"### {scene}")

            for v in scene_voices:
                if count >= max_voices:
                    break

                name = v.get("音色名称", "")
                voice_type = v.get("voice_type", "")
                abilities = v.get("支持能力", "")

                lines.append(f"- {name} | `{voice_type}` | {abilities}")
                count += 1

            lines.append("")

        lines.append("## 音色选择规则")
        lines.append("根据 archetype 和 attitude 选择最合适的音色：")
        lines.append("- 观察者 + curious → 选择知性、沉稳风格的音色（如 知性灿灿、云舟）")
        lines.append("- 讲故事的人 + playful → 选择活泼、亲和风格的音色（如 爽快思思、小天）")
        lines.append("- 追问者 + skeptical → 选择专业、理性风格的音色（如 刘飞、知性灿灿）")
        lines.append("- 吐槽者 + playful → 选择幽默、直率风格的音色（如 猴哥、佩奇猪）")
        lines.append("- 理想主义者 + passionate → 选择富有表现力的音色（如 Vivi、少年梓辛）")
        lines.append("")
        lines.append("选择后，将 voice_type 填入 expression.voice_id 字段。")

        return "\n".join(lines)

    def suggest_voice(self, archetype: str, attitude: str, gender: str = "female", age_group: str = None) -> str:
        """
        根据 archetype、attitude 和 age_group 推荐默认音色
        优先级：性别 > 年龄 > 性格特征

        Args:
            archetype: 原型角色
            attitude: 态度
            gender: 性别
            age_group: 年龄段 (youth/young:青年, middle_aged:中年, senior:老年)，None表示自动推断

        Returns:
            推荐的 voice_type
        """
        voices = self.get_voices_by_gender(gender)

        # 按年龄段分类的音色映射（基于音色描述中的年龄和性格特征）
        age_voice_mapping = {
            "male": {
                "youth": [
                    "zh_male_shaonianzixin_uranus_bigtts",   # 少年梓辛：少年感、清爽阳光
                    "zh_male_xiaotian_uranus_bigtts",        # 小天：男大、清澈温润
                    "zh_male_ruyayichen_uranus_bigtts"       # 儒雅逸辰：稳重青年、温柔成熟
                ],
                "middle_aged": [
                    "zh_male_liufei_uranus_bigtts",          # 刘飞：逻辑清晰、理性稳重
                    "zh_male_yunzhou_uranus_bigtts"          # 云舟：声音磁性、成熟理性
                ],
                "senior": [
                    "zh_male_dayi_uranus_bigtts"             # 大壹：历经世事的沉稳大叔
                ],
            },
            "female": {
                "youth": [
                    "zh_female_xiaohe_uranus_bigtts",        # 小何：甜美有活力、活泼开朗
                    "zh_female_linjianvhai_uranus_bigtts",   # 邻家女孩：软糯温柔、低调内敛
                    "zh_female_sajiaoxuemei_uranus_bigtts",  # 撒娇学妹：嗲甜软萌、灵动娇气
                    "zh_female_shuangkuaisisi_uranus_bigtts" # 爽快思思：温暖直爽、阳光热情
                ],
                "middle_aged": [
                    "zh_female_cancan_uranus_bigtts",        # 知性灿灿：温柔舒缓、治愈系
                    "zh_female_meilinvyou_uranus_bigtts",    # 魅力女友：性感妩媚、成熟魅力
                    "zh_female_qingxinnvsheng_uranus_bigtts",# 清新女声：职场精英、明媚大方
                    "zh_female_meilisufei_uranus_bigtts",    # 魅力苏菲：高冷御姐、内心细腻
                    "zh_female_jitangnv_uranus_bigtts",      # 鸡汤女：知心姐姐、温柔体贴
                    "zh_female_heimao_uranus_bigtts"         # 黑猫侦探社咪仔：稳重优雅、温暖亲和
                ],
                "senior": [
                    "zh_female_jitangnv_uranus_bigtts",      # 鸡汤女：稳重优雅知心姐姐
                    "zh_female_heimao_uranus_bigtts"         # 黑猫侦探社咪仔：稳重优雅、善于陪伴
                ],
            }
        }

        # 构建性格推荐映射（不含年龄偏见的通用推荐）
        recommendations = {
            ("观察者", "curious"): ["zh_female_cancan_uranus_bigtts", "zh_male_m191_uranus_bigtts"],
            ("讲故事的人", "playful"): ["zh_female_shuangkuaisisi_uranus_bigtts", "zh_male_taocheng_uranus_bigtts"],
            ("追问者", "skeptical"): ["zh_female_cancan_uranus_bigtts", "zh_male_liufei_uranus_bigtts"],
            ("吐槽者", "playful"): ["zh_female_shuangkuaisisi_uranus_bigtts", "zh_male_taocheng_uranus_bigtts"],
            ("理想主义者", "passionate"): ["zh_female_vv_uranus_bigtts", "zh_male_liufei_uranus_bigtts"],  # 男性改为刘飞（成熟）
            ("观察者", "playful"): ["zh_female_linjianvhai_uranus_bigtts", "zh_male_taocheng_uranus_bigtts"],
            ("讲故事的人", "curious"): ["zh_female_xiaohe_uranus_bigtts", "zh_male_ruyayichen_uranus_bigtts"],
        }

        # 第一步：如果指定了年龄段，优先从该年龄段选择
        if age_group and age_group in ["youth", "middle_aged", "senior"]:
            age_choices = age_voice_mapping.get(gender, {}).get(age_group, [])

            # 查找该年龄段中符合性格推荐的音色
            key = (archetype, attitude)
            if key in recommendations:
                for voice_type in recommendations[key]:
                    if voice_type in age_choices:
                        # 检查音色是否存在于可用列表中
                        if any(v.get("voice_type") == voice_type for v in voices):
                            return voice_type

            # 如果性格匹配失败，从年龄段默认选择
            for voice_type in age_choices:
                if any(v.get("voice_type") == voice_type for v in voices):
                    return voice_type

        # 第二步：使用通用性格推荐（已去除明显的年龄偏见）
        key = (archetype, attitude)
        if key in recommendations:
            for voice_type in recommendations[key]:
                # 检查是否存在于列表中
                if any(v.get("voice_type") == voice_type for v in voices):
                    return voice_type

        # 默认回退（根据年龄调整默认值）
        default_map = {
            ("female", "youth"): "zh_female_xiaohe_uranus_bigtts",           # 小何：甜美有活力
            ("female", "middle_aged"): "zh_female_cancan_uranus_bigtts",     # 知性灿灿：温柔治愈
            ("female", "senior"): "zh_female_jitangnv_uranus_bigtts",        # 鸡汤女：知心姐姐
            ("male", "youth"): "zh_male_shaonianzixin_uranus_bigtts",        # 少年梓辛：清爽阳光
            ("male", "middle_aged"): "zh_male_liufei_uranus_bigtts",         # 刘飞：理性稳重
            ("male", "senior"): "zh_male_dayi_uranus_bigtts",                # 大壹：沉稳大叔
        }

        # 根据性别和年龄段返回默认值
        if age_group in ["youth", "middle_aged", "senior"]:
            return default_map.get((gender, age_group), default_map.get((gender, "middle_aged")))

        # 最后的保底回退
        return "zh_female_cancan_uranus_bigtts" if gender == "female" else "zh_male_liufei_uranus_bigtts"


