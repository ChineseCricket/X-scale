---
name: self-similar-model
description: Kaiser (1986) self-similar model 推导及标度关系预言
provenance: llm-derived
---

# Self-similar Model (Kaiser 1986)

## 基本假设

在纯引力塌缩框架下，所有团簇是 scaled versions of each other（strong self-similarity, Bower 1997）。

## 关键推导

### Virial temperature
$$kT \propto M^{2/3} \rho^{1/3} \propto M^{2/3} E(z)^{2/3}$$

### Bolometric luminosity
$$L_X \propto n_e^2 \Lambda(T) V \propto M \rho_{\text{gas}} T^{1/2}$$

### Self-similar slopes

| Relation | Slope | E(z) exponent |
|----------|-------|---------------|
| $T_X - M_{500}$ | $T \propto M^{2/3}$ | $E(z)^{2/3}$ |
| $L_X - M_{500}$ | $L \propto M^{4/3}$ | $E(z)^{-7/3}$ (bolometric) |
| $L_X - T_X$ | $L \propto T^2$ | $E(z)^{-1}$ |
| $Y_X - M_{500}$ | $Y_X \propto M^{5/3}$ | $E(z)^{2/3}$ |
| $M_{\text{gas}} - M_{500}$ | $M_{\text{gas}} \propto M$ | $E(z)^0$ (const fgas) |

## 偏离 self-similar 的原因

- AGN feedback 加热中心区域（主要在 r < 0.15R500）
- Radiative cooling 导致低质量团 gas fraction 下降
- Merger shocks 提升外围 entropy
- 结果：Lx-M 斜率观测值 ~1.3–2.0，比 4/3 更陡

## 相关概念
- [[scaling_relations]] — 观测结果对比
- [[spectral_fitting]] — T_X 和 L_X 的测量方法
