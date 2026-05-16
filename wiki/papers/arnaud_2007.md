---
title: "Calibration of the galaxy cluster M500-YX relation with XMM-Newton"
authors: [Arnaud, M., Pointecouteau, E., Pratt, G.W.]
year: 2007
journal: "A&A, 474, L37"
arxiv: "0709.1561"
keywords: [scaling-relations, M500-YX, REXCESS, XMM-Newton, mass-proxy]
sample_size: 10
redshift_range: [0.02, 0.15]
mass_range: ["~1e13", "~1e15"]
---

# Arnaud et al. (2007)

## One-line Summary
标定 M500-YX 关系（YX = TX × Mgas），斜率接近 self-similar (3/5)，确认 YX 为低 scatter 质量代理。

## Sample
10 个 relaxed 近邻团（同 Arnaud+05），YX 范围 $10^{13}$–$10^{15} M_\odot$ keV。

## Key Results

### M_500 - Y_X
- Slope: $\alpha = 0.548 \pm 0.027$ — close to self-similar ($3/5 = 0.6$)
- 与质量范围无关
- Normalization: 比含 cooling+feedback 的数值模拟低 ~20%
- 可能原因: HSE 质量低估 / 模拟中热气体比例低估

### YX vs TX vs Mgas as mass proxy
- YX 的 intrinsic scatter 低于 TX 和 Mgas,500
- 支持 YX 作为最优质量代理

## Key Equations
$$h(z)^{2/5} M_{500} = 10^{14.556 \pm 0.015} \left(\frac{Y_X}{2 \times 10^{14} M_\odot \text{ keV}}\right)^{0.548 \pm 0.027}$$

## Methods
- Instrument: XMM-Newton
- YX = TX × Mgas,500（Kravtsov+06 定义）
- Mass: HSE + NFW (同 Arnaud+05)

## Relations to Other Work
- [[arnaud_2005]] — 同一样本的 M-T 关系
- [[pratt_2009]] — 用此 YX-M 关系迭代估计 R500
- [[mantz_2010]] — 使用 YX 作为质量代理
