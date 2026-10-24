"""fidelitygate/adaptive/uncertainty_updater.py
Dedicated uncertainty interval updater enforcing bounded-error intersection and inconsistency detection.
Guarantees that only justified parameter intervals are updated while preserving unrelated dimensions.
"""

import uuid
from typing import Dict, List, Optional, Tuple

from .models import (
    DiagnosticObservation,
    UncertaintyInterval,
    UncertaintyUpdate,
)


class InconsistentMeasurementError(Exception):
    """Raised when an empirical measurement interval is disjoint from prior model bounds."""
    pass


class UncertaintyUpdater:
    """Updates parameter uncertainty intervals via mathematically rigorous interval intersection."""

    def update_parameter_uncertainty(
        self,
        parameter_name: str,
        target_entity: str,
        prior_interval: UncertaintyInterval,
        observation: DiagnosticObservation,
    ) -> UncertaintyUpdate:
        """
        Intersects prior uncertainty interval with observation confidence interval:
        Theta_new = [max(prior_min, y - delta), min(prior_max, y + delta)]
        """
        update_id = f"upd-{uuid.uuid4().hex[:8]}"

        # 1. Parameter and Entity Compatibility Check
        if observation.target_parameter != parameter_name:
            raise ValueError(
                f"Parameter mismatch: observation measures '{observation.target_parameter}', "
                f"cannot update target parameter '{parameter_name}'."
            )

        if not observation.is_valid:
            return UncertaintyUpdate(
                update_id=update_id,
                parameter_name=parameter_name,
                target_entity=target_entity,
                prior_interval=prior_interval,
                measurement_interval=observation.confidence_interval,
                posterior_interval=prior_interval,
                is_consistent=False,
                justification="Observation is marked invalid or unavailable; prior interval preserved unchanged.",
                assumptions=["No valid empirical evidence acquired."],
            )

        # 2. Strict Dimensional / Unit Compatibility Check
        if observation.unit != prior_interval.unit:
            return UncertaintyUpdate(
                update_id=update_id,
                parameter_name=parameter_name,
                target_entity=target_entity,
                prior_interval=prior_interval,
                measurement_interval=observation.confidence_interval,
                posterior_interval=prior_interval,
                is_consistent=False,
                justification=(
                    f"Dimensional mismatch: parameter '{parameter_name}' has unit '{prior_interval.unit}', "
                    f"but observation provides interval in incompatible unit '{observation.unit}'. "
                    f"Bounded interval intersection requires matching physical dimensions."
                ),
                assumptions=["Observation cannot be directly intersected without dimensional conversion."],
            )

        # 2. Extract Intervals
        prior_min = prior_interval.min_value
        prior_max = prior_interval.max_value
        meas_min, meas_max = observation.confidence_interval

        # 3. Compute Intersection
        new_min = max(prior_min, meas_min)
        new_max = min(prior_max, meas_max)

        # 4. Check for Empty Intersection (Inconsistency)
        if new_min > new_max:
            # Disjoint intervals: prior model assumptions contradict empirical measurement
            return UncertaintyUpdate(
                update_id=update_id,
                parameter_name=parameter_name,
                target_entity=target_entity,
                prior_interval=prior_interval,
                measurement_interval=(meas_min, meas_max),
                posterior_interval=None,
                is_consistent=False,
                justification=(
                    f"Inconsistency detected: empirical measurement interval [{meas_min}, {meas_max}] {prior_interval.unit} "
                    f"is disjoint from prior model uncertainty [{prior_min}, {prior_max}] {prior_interval.unit}. "
                    f"Empty intersection rejected to prevent false certainty."
                ),
                assumptions=["Prior model bounds and diagnostic measurement are mutually incompatible."],
            )

        # 5. Valid Posterior Uncertainty Interval
        posterior_nom = round((new_min + new_max) / 2.0, 4)
        posterior = UncertaintyInterval(
            parameter_name=parameter_name,
            unit=prior_interval.unit,
            min_value=round(new_min, 4),
            max_value=round(new_max, 4),
            nominal_value=posterior_nom,
            confidence_level=prior_interval.confidence_level,
            is_bounded=True,
        )

        reduction_pct = round((1.0 - (posterior.width / max(prior_interval.width, 1e-6))) * 100.0, 1)
        justification = (
            f"Successfully updated '{parameter_name}' on '{target_entity}'. "
            f"Interval narrowed from [{prior_min}, {prior_max}] to [{posterior.min_value}, {posterior.max_value}] "
            f"({reduction_pct}% uncertainty reduction) via bounded-error intersection with [{meas_min}, {meas_max}]."
        )

        return UncertaintyUpdate(
            update_id=update_id,
            parameter_name=parameter_name,
            target_entity=target_entity,
            prior_interval=prior_interval,
            measurement_interval=(meas_min, meas_max),
            posterior_interval=posterior,
            is_consistent=True,
            justification=justification,
            assumptions=[
                f"Measurement error bounded by ±{observation.declared_error_bound} {observation.unit}.",
                "Prior model and sensor error distributions satisfy interval intersection axioms.",
            ],
        )

    def update_uncertainty_state(
        self,
        current_state: Dict[str, UncertaintyInterval],
        observation: DiagnosticObservation,
        target_entity: str,
    ) -> Tuple[Dict[str, UncertaintyInterval], UncertaintyUpdate]:
        """
        Updates only the specific parameter measured, strictly preserving all other dimensions.
        """
        target_param = observation.target_parameter
        if target_param not in current_state:
            raise KeyError(f"Parameter '{target_param}' not found in current uncertainty state dictionary.")

        prior = current_state[target_param]
        update_record = self.update_parameter_uncertainty(
            parameter_name=target_param,
            target_entity=target_entity,
            prior_interval=prior,
            observation=observation,
        )

        new_state = dict(current_state)
        if update_record.is_consistent and update_record.posterior_interval is not None:
            new_state[target_param] = update_record.posterior_interval

        return new_state, update_record

