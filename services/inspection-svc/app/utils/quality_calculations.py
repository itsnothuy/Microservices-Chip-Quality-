"""
Quality calculation utilities.

Helper functions for quality metric calculations and statistical analysis.
"""

import math
from decimal import Decimal
from typing import Dict, List


def calculate_weighted_score(
    scores: Dict[str, Decimal],
    weights: Dict[str, Decimal]
) -> Decimal:
    """
    Calculate weighted average score.
    
    Args:
        scores: Dictionary of metric scores
        weights: Dictionary of metric weights (should sum to 1.0)
        
    Returns:
        Weighted average score
    """
    if not scores or not weights:
        return Decimal("0.0")
    
    total_score = Decimal("0.0")
    total_weight = Decimal("0.0")
    
    for metric, score in scores.items():
        weight = weights.get(metric, Decimal("0.0"))
        total_score += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return Decimal("0.0")
    
    return total_score / total_weight


def calculate_defect_density(
    defect_count: int,
    area: Decimal,
    unit: str = "cm2"
) -> Decimal:
    """
    Calculate defect density (defects per unit area).
    
    Args:
        defect_count: Number of defects
        area: Total area inspected
        unit: Area unit (default: cm2)
        
    Returns:
        Defect density
    """
    if area <= 0:
        return Decimal("0.0")
    
    return Decimal(defect_count) / area


def calculate_process_capability(
    measurements: List[Decimal],
    lower_spec: Decimal,
    upper_spec: Decimal
) -> Dict[str, Decimal]:
    """
    Calculate process capability indices (Cp, Cpk).
    
    Args:
        measurements: List of measurement values
        lower_spec: Lower specification limit
        upper_spec: Upper specification limit
        
    Returns:
        Dictionary with Cp and Cpk values
    """
    if not measurements or len(measurements) < 2:
        return {"Cp": Decimal("0.0"), "Cpk": Decimal("0.0")}
    
    # Calculate mean and standard deviation
    mean = sum(measurements) / Decimal(len(measurements))
    variance = sum((x - mean) ** 2 for x in measurements) / Decimal(len(measurements) - 1)
    std_dev = Decimal(math.sqrt(float(variance)))
    
    if std_dev == 0:
        return {"Cp": Decimal("0.0"), "Cpk": Decimal("0.0")}
    
    # Calculate Cp (process capability)
    cp = (upper_spec - lower_spec) / (6 * std_dev)
    
    # Calculate Cpk (process capability index)
    cpu = (upper_spec - mean) / (3 * std_dev)
    cpl = (mean - lower_spec) / (3 * std_dev)
    cpk = min(cpu, cpl)
    
    return {
        "Cp": cp,
        "Cpk": cpk,
        "mean": mean,
        "std_dev": std_dev
    }


def calculate_yield_rate(
    passed_count: int,
    total_count: int
) -> Decimal:
    """
    Calculate yield rate (percentage of passed units).
    
    Args:
        passed_count: Number of units that passed
        total_count: Total number of units
        
    Returns:
        Yield rate as decimal (0-1)
    """
    if total_count == 0:
        return Decimal("0.0")
    
    return Decimal(passed_count) / Decimal(total_count)


def calculate_dpmo(
    defect_count: int,
    opportunity_count: int,
    unit_count: int
) -> Decimal:
    """
    Calculate Defects Per Million Opportunities (DPMO).
    
    Args:
        defect_count: Total number of defects
        opportunity_count: Number of defect opportunities per unit
        unit_count: Number of units inspected
        
    Returns:
        DPMO value
    """
    if opportunity_count == 0 or unit_count == 0:
        return Decimal("0.0")
    
    total_opportunities = opportunity_count * unit_count
    dpmo = (Decimal(defect_count) / Decimal(total_opportunities)) * Decimal("1000000")
    
    return dpmo


def normalize_score(
    value: Decimal,
    min_value: Decimal,
    max_value: Decimal
) -> Decimal:
    """
    Normalize a value to 0-1 range.
    
    Args:
        value: Value to normalize
        min_value: Minimum possible value
        max_value: Maximum possible value
        
    Returns:
        Normalized value (0-1)
    """
    if max_value == min_value:
        return Decimal("0.5")
    
    normalized = (value - min_value) / (max_value - min_value)
    
    # Clamp to 0-1 range
    return max(Decimal("0.0"), min(Decimal("1.0"), normalized))


def calculate_confidence_interval(
    mean: Decimal,
    std_dev: Decimal,
    sample_size: int,
    confidence_level: Decimal = Decimal("0.95")
) -> Dict[str, Decimal]:
    """
    Calculate confidence interval for quality metrics.
    
    Args:
        mean: Sample mean
        std_dev: Sample standard deviation
        sample_size: Number of samples
        confidence_level: Confidence level (default 0.95 for 95%)
        
    Returns:
        Dictionary with lower and upper bounds
    """
    if sample_size < 2:
        return {"lower": mean, "upper": mean}
    
    # Using z-score for large samples (approximation)
    z_score = Decimal("1.96") if confidence_level == Decimal("0.95") else Decimal("2.576")
    
    margin_of_error = z_score * (std_dev / Decimal(math.sqrt(sample_size)))
    
    return {
        "lower": mean - margin_of_error,
        "upper": mean + margin_of_error,
        "margin_of_error": margin_of_error
    }
