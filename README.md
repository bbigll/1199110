# Texas Hold'em AI（简化版）

这是一个用 Python 写的德州扑克 AI 决策示例程序：

- 输入你的手牌 + 公共牌
- 指定对手人数
- 通过蒙特卡洛模拟估算胜率
- 输出 Fold / Call / Raise 建议

## 运行

```bash
python3 texas_ai.py
```

## 输入示例

- 手牌：`As Kh`
- 公共牌：`Td Jc 2s`

牌面格式：
- 点数：`2-9 T J Q K A`
- 花色：`c d h s`

例如：`Ah` = 红桃A，`Tc` = 梅花10。

## 说明

- 这是教学/演示用途，并非 GTO 级别博弈引擎。
- 建议动作基于胜率阈值和底池赔率的简化规则。
