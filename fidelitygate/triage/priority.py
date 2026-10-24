import math
from typing import Optional
from .models import FindingSeverity, LabelOrigin


class PriorityScorer:
    """Calculates transparent severity categories and independent confidence scores."""

    @staticmethod
    def calculate_severity(
        metric_name: str,
        observed_value: float,
        baseline_value: Optional[float],
        deviation_score: Optional[float],
        label_origin: LabelOrigin,
        entity_id: str,
    ) -> FindingSeverity:
        # 1. Source-defined critical events (e.g. BGP clear on core infrastructure or high FIB drops)
        is_core_entity = any(k in entity_id.lower() for k in ["spine", "core", "dr01", "dr02"])
        
        # FIB packet drop surges are critical in forwarding plane
        if "drop" in metric_name.lower():
            if observed_value >= 1000.0:
                return FindingSeverity.CRITICAL
            elif observed_value >= 100.0:
                return FindingSeverity.HIGH if is_core_entity else FindingSeverity.MEDIUM
            elif observed_value > 0.0:
                return FindingSeverity.LOW

        # 2. Score-based statistical deviations
        if deviation_score is not None:
            abs_z = abs(deviation_score)
            if abs_z >= 7.0:
                return FindingSeverity.CRITICAL if is_core_entity else FindingSeverity.HIGH
            elif abs_z >= 4.5:
                return FindingSeverity.HIGH
            elif abs_z >= 3.0:
                return FindingSeverity.MEDIUM
            else:
                return FindingSeverity.LOW

        # 3. Source-defined event baseline
        if label_origin == LabelOrigin.SOURCE_DEFINED:
            return FindingSeverity.HIGH if is_core_entity else FindingSeverity.MEDIUM

        # 4. Fallback when deviation score is unavailable (e.g. invariant baseline step change)
        if baseline_value is not None:
            diff = abs(observed_value - baseline_value)
            if "cpu" in metric_name.lower():
                if observed_value >= 80.0:
                    return FindingSeverity.CRITICAL
                elif observed_value >= 50.0:
                    return FindingSeverity.HIGH
                elif diff >= 20.0:
                    return FindingSeverity.MEDIUM
            if baseline_value > 0:
                rel = diff / baseline_value
                if rel >= 1.0 or observed_value >= 80.0:
                    return FindingSeverity.HIGH
                elif rel > 0.3:
                    return FindingSeverity.MEDIUM
                else:
                    return FindingSeverity.LOW
            elif diff > 0:
                return FindingSeverity.HIGH if diff >= 100.0 else FindingSeverity.MEDIUM

        return FindingSeverity.LOW

    @staticmethod
    def calculate_confidence(
        sample_count: int,
        label_origin: LabelOrigin,
        quality_status: str,
        unit: Optional[str],
        has_mad_fallback: bool = False,
    ) -> float:
        """Computes epistemic confidence in finding validity, strictly decoupled from severity."""
        if label_origin == LabelOrigin.SOURCE_DEFINED:
            base = 0.95
        elif label_origin == LabelOrigin.STATISTICAL_DETECTOR:
            # More baseline samples increase confidence up to 0.88
            base = min(0.50 + (sample_count * 0.015), 0.88)
        elif label_origin == LabelOrigin.RULE_BASED:
            base = 0.75
        else:
            base = 0.50

        # Adjust for data quality defects
        if quality_status == "SUSPECT":
            base -= 0.20
        elif quality_status == "UNKNOWN":
            base -= 0.30

        # Undocumented unit penalty
        if unit is None:
            base -= 0.10

        # Fallback variance penalty
        if has_mad_fallback:
            base -= 0.15

        return round(max(min(base, 0.99), 0.10), 2)
