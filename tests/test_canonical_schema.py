from __future__ import annotations

from ai4s_legitimacy.collection.canonical_schema import normalize_claim_units


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
            "evidence": ["先用AI分析，再自己复核结果。"],
        }
    ]
