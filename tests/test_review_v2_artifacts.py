from __future__ import annotations

import ai4s_legitimacy.collection.review_v2_artifacts as review_v2_artifacts


def test_bootstrap_inclusion_handles_uppercase_ai_tokens() -> None:
    text = (
        "10分钟搞定文献综述！AI辅助！全流程演示！ "
        "本视频主要讲解了如何利用AI（GPT）辅助进行文献综述写作的效率提升。"
        "严肃声明：AI绝不可以代替思考，务必只把AI当作提效工具！"
    )

    workflow_codes, legitimacy_codes, evaluation_codes, boundary_codes = (
        review_v2_artifacts._manual_or_bootstrap_codes(None, text=text)
    )

    assert "A1.2" in workflow_codes
    assert "A1.9" in workflow_codes
    assert "B2" in legitimacy_codes
    assert "D1" in boundary_codes

    decision = review_v2_artifacts._bootstrap_inclusion_decision(
        text=text,
        workflow_codes=workflow_codes,
        legitimacy_codes=legitimacy_codes,
        evaluation_codes=evaluation_codes,
        boundary_codes=boundary_codes,
        historical_status="review_needed",
        suggestion_status="review_needed",
    )

    assert decision == "纳入"
