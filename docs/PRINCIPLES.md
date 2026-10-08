# ZERO CODE — Mission and Principles

## Mission
**人間とAIが共に進化し、挑戦を成長に変える。**

Human and AI evolve together, turning challenges into growth.

## Motto
**原則は守る。方法は進化させる。結果から学び続ける。**

Protect the principles. Evolve the methods. Keep learning from outcomes.

## Operating principles
1. **挑戦を止めない。** Try small, reversible experiments; do not confuse recklessness with courage.
2. **事実に向き合う。** Measure actual results; never fabricate metrics, outcomes, or test success.
3. **失敗を資産に変える。** Record the decision, evidence, unexpected outcome, and lesson.
4. **互いの判断を尊重し、検証する。** Humans and AI can both be wrong; important decisions need evidence and review.
5. **成長を仕組みにする。** Make learning repeatable through tests, documented decisions, and shared processes.

## Engineering decision hierarchy
Safety > reliability > development speed.

- Protect customer and project data; preserve reversibility.
- Prefer small PRs with test evidence and a rollback path.
- Production database changes, infrastructure apply, and new paid services require explicit human approval.
- Document tradeoffs when changing an earlier decision.

## Decision journal template
For a consequential technical or business decision, record:
- Date and context
- Goal and constraints
- Options considered and evidence
- Chosen option and why
- Expected result and how it will be measured
- Actual result (once observed)
- Lessons and whether the rule or method should change

This document captures guiding principles, not immutable technical choices.
Changes to these principles should be deliberate, explained, and approved by the human project owner.
