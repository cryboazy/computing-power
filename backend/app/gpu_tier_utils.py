from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.local_models import LocalGpuTierDict


class GPUTierManager:
    DEFAULT_TIERS = {
        1: {"label": "高端卡", "key": "high"},
        2: {"label": "中端卡", "key": "medium"},
        3: {"label": "低端卡", "key": "low"}
    }

    def __init__(self, db: Session):
        self.db = db
        self._cache = None

    def _load_tiers(self) -> Dict[int, Dict]:
        if self._cache is not None:
            return self._cache

        tiers = self.db.query(LocalGpuTierDict).filter(
            LocalGpuTierDict.dict_type == "gpu_tier",
            LocalGpuTierDict.status == 1,
            LocalGpuTierDict.deleted == 0
        ).order_by(LocalGpuTierDict.dict_sort).all()

        self._cache = {}
        for tier in tiers:
            self._cache[tier.dict_value] = {
                "label": tier.dict_label,
                "key": tier.dict_label,
                "id": tier.id
            }

        if not self._cache:
            self._cache = self.DEFAULT_TIERS.copy()

        return self._cache

    def invalidate_cache(self):
        self._cache = None

    def get_tier_label(self, card_type: int) -> str:
        tiers = self._load_tiers()
        tier = tiers.get(card_type)
        if tier:
            return tier["label"]
        return self.DEFAULT_TIERS.get(card_type, {}).get("label", "未知")

    def get_tier_key(self, card_type: int) -> str:
        tiers = self._load_tiers()
        tier = tiers.get(card_type)
        if tier:
            return tier["key"]
        default = self.DEFAULT_TIERS.get(card_type, {})
        return default.get("key", "unknown")

    def get_all_tiers(self) -> List[Dict]:
        tiers = self._load_tiers()
        return [
            {"value": k, "label": v["label"], "name": v["label"]}
            for k, v in sorted(tiers.items())
        ]

    def get_label_map(self) -> Dict[int, str]:
        tiers = self._load_tiers()
        result = {}
        for card_type, tier_info in tiers.items():
            result[card_type] = tier_info["label"]

        for card_type, default_info in self.DEFAULT_TIERS.items():
            if card_type not in result:
                result[card_type] = default_info["label"]

        return result

    def calculate_tier_counts(self, gpu_infos: Dict, devices: List) -> Dict[str, int]:
        tiers = self._load_tiers()

        tier_counts = {}
        for card_type, tier_info in tiers.items():
            tier_counts[tier_info["label"]] = 0
        tier_counts["未知"] = 0

        tier_label_map = self.get_label_map()

        for device in devices:
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            gpu_count = device.gpu_count or 1

            if gpu_info:
                tier_label = tier_label_map.get(gpu_info.card_type)
                if tier_label and tier_label in tier_counts:
                    tier_counts[tier_label] += gpu_count
                else:
                    tier_counts["未知"] += gpu_count
            else:
                tier_counts["未知"] += gpu_count

        return tier_counts

    def format_tier_result(self, tier_counts: Dict) -> List[Dict]:
        result = []
        for label, count in tier_counts.items():
            result.append({
                "name": label,
                "value": count
            })
        return result

    def format_tier_by_org_result(self, tier_counts: Dict, org_name: str) -> Dict:
        result = {
            "org_name": org_name
        }

        for label, count in tier_counts.items():
            result[label] = count

        result["total"] = sum(tier_counts.values())

        return result
