from __future__ import annotations

from ai4s_legitimacy.collection.canonical_schema import normalize_claim_units

V2_EMPTY_FIELDS = {
    "ai_intervention_mode_codes": [],
    "ai_intervention_intensity_codes": [],
    "evaluation_tension_codes": [],
    "formal_norm_reference_codes": [],
    "boundary_mechanism_codes": [],
    "boundary_result_codes": [],
}


def test_normalize_claim_units_accepts_labelled_workflow_codes() -> None:
    normalized = normalize_claim_units(
        [
            {
                "practice_unit": "AI辅助文献综述",
                "workflow_stage_codes": ["A1.2 文献调研与知识整合"],
                "legitimacy_codes": ["B0 未表达评价"],
                "basis_codes": [{"code": "C1 效率", "evidence": "更快"}],
                "boundary_codes": [],
                "boundary_mode_codes": [],
                "evidence": ["使用AI梳理论文综述框架。"],
            }
        ]
    )

    assert normalized == [
        {
            "practice_unit": "AI辅助文献综述",
            "workflow_stage_codes": ["A1.2"],
            "legitimacy_codes": ["B0"],
            "basis_codes": [{"code": "C1", "evidence": "更快"}],
            "boundary_codes": [],
            "boundary_mode_codes": [],
            **V2_EMPTY_FIELDS,
            "evidence": ["使用AI梳理论文综述框架。"],
        }
    ]


def test_normalize_claim_units_accepts_dict_legitimacy_codes() -> None:
    normalized = normalize_claim_units(
        [
            {
                "practice_unit": "AI辅助数据分析",
                "workflow_stage_codes": [{"code": "A1.6 数据处理与分析建模"}],
                "legitimacy_codes": [{"code": "B2 有条件接受", "evidence": "需人工核查"}],
                "basis_codes": [{"code": "C8 结果可靠性/可验证性", "evidence": "需人工核查"}],
                "boundary_codes": [{"code": "D1.10 验证/复核边界", "evidence": "需人工核查"}],
                "boundary_mode_codes": [{"code": "D2.5 要求人类最终审核", "evidence": "需人工核查"}],
                "evidence": ["先用AI分析，再自己复核结果。"],
            }
        ]
    )

    assert normalized == [
        {
            "practice_unit": "AI辅助数据分析",
            "workflow_stage_codes": ["A1.6"],
            "legitimacy_codes": ["B2"],
            "basis_codes": [{"code": "C8", "evidence": "需人工核查"}],
            "boundary_codes": [{"code": "D1.10", "evidence": "需人工核查"}],
            "boundary_mode_codes": [{"code": "D2.5", "evidence": "需人工核查"}],
            **V2_EMPTY_FIELDS,
            "evidence": ["先用AI分析，再自己复核结果。"],
        }
    ]


def test_normalize_claim_units_preserves_optional_framework_v2_fields() -> None:
    normalized = normalize_claim_units(
        [
            {
                "practice_unit": "AI辅助审稿治理",
                "workflow_stage_codes": ["A2.7 出版与评审治理"],
                "legitimacy_codes": ["B2 有条件接受"],
                "basis_codes": [{"code": "C9 公平与透明", "evidence": "排序要透明"}],
                "boundary_codes": [{"code": "D1.12 科研治理边界", "evidence": "审稿排序"}],
                "boundary_mode_codes": [],
                "ai_intervention_mode_codes": ["F6 治理监督"],
                "ai_intervention_intensity_codes": ["G2 中强度共创"],
                "evaluation_tension_codes": ["H6 自动化治理 vs 公平透明"],
                "formal_norm_reference_codes": ["I6 审稿规范"],
                "boundary_mechanism_codes": ["J3 规范化机制"],
                "boundary_result_codes": ["K6 治理争议化"],
                "evidence": ["AI 可以辅助筛稿，但排序规则必须透明。"],
            }
        ]
    )

    assert normalized == [
        {
            "practice_unit": "AI辅助审稿治理",
            "workflow_stage_codes": ["A2.7"],
            "legitimacy_codes": ["B2"],
            "basis_codes": [{"code": "C9", "evidence": "排序要透明"}],
            "boundary_codes": [{"code": "D1.12", "evidence": "审稿排序"}],
            "boundary_mode_codes": [],
            "ai_intervention_mode_codes": ["F6"],
            "ai_intervention_intensity_codes": ["G2"],
            "evaluation_tension_codes": ["H6"],
            "formal_norm_reference_codes": ["I6"],
            "boundary_mechanism_codes": ["J3"],
            "boundary_result_codes": ["K6"],
            "evidence": ["AI 可以辅助筛稿，但排序规则必须透明。"],
        }
    ]
