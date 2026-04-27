from __future__ import annotations

from ai4s_legitimacy.analysis.quality_v5_consistency import (
    build_parser,
    evaluate_quality_v5_consistency,
    export_quality_v5_consistency,
    main,
    write_quality_v5_consistency_report,
)

evaluate_quality_v4_consistency = evaluate_quality_v5_consistency
write_quality_v4_consistency_report = write_quality_v5_consistency_report
export_quality_v4_consistency = export_quality_v5_consistency

__all__ = [
    "build_parser",
    "evaluate_quality_v4_consistency",
    "evaluate_quality_v5_consistency",
    "export_quality_v4_consistency",
    "export_quality_v5_consistency",
    "main",
    "write_quality_v4_consistency_report",
    "write_quality_v5_consistency_report",
]
