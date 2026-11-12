# 宏观背景与跨资产状态模块

源方法：[macro-regime-detector](../vendor/tradermonty/skills/macro-regime-detector/SKILL.md)。六分量规则、权重和解释读取随包 `references/regime_detection_methodology.md`、`indicator_interpretation_guide.md`。

## 适用范围

该模型主要用美国ETF、美国收益率/其备用比率表达美元跨资产环境，观察1—2年结构转变。它是状态识别和确认，常有数周/月滞后，不是精确宏观预测器。

六分量：RSP/SPY集中度、10Y–2Y曲线、HYG/LQD信用、IWM/SPY大小盘、SPY/TLT及相关性、XLY/XLP周期防御。输出集中/扩散/收缩/通胀/过渡状态和信号强弱。备用SHY/TLT不是原始利差，必须注明实际路径及数据缺口。

## 使用脚本

- 依赖通常为Python、requests、yfinance；FMP可选。先 `research.py doctor`，不因缺少FMP自动要求用户提供Key，可按源方法使用无Key路径。
- `vendor/tradermonty/skills/macro-regime-detector/scripts/macro_regime_detector.py` 是原始固定版。读取其 `--help` 与静态导入后，从 `vendor/tradermonty/` 为工作目录运行（用宿主 workdir，不修改用户目录）。
- 本项目已在 `06_AI与自动化/runtime/ai-investment-research/venv/` 准备可选行情环境。优先用融合适配器：`python "SKILL_ROOT/scripts/run_macro.py" --output-dir "ABS_RUN_DIR/02_analysis/macro" --as-of YYYY-MM-DD`；它从技能真实路径探测项目内环境，搬迁后可用 `--python ABS_PYTHON` 指定。`--probe` 只验证导入，不取行情。
- **固定版本的宏观脚本获取当前数据，不具备历史时点输入接口**。适配器拒绝历史/未来 `as_of` 的实时获取；回看历史必须另用已冻结、在截止日前可知的序列或记缺口，不能用当前价格冒充历史可知数据。
- 只向本次 `02_analysis/macro/` 输出。不要将Key放 `--api-key` 参数；按环境变量安全注入。网络请求失败、数据过旧或所有分量不可用时不能记录有效结论。
- 若上游真实脚本需要已取回的共享模块，用包中原始目录保持其相对导入；缺包/不兼容则报告原因，用实际可得数据做明确标为“定性”的背景，不仿造脚本分数。

## A股/港股适配

研究A股/港股时，美国模型只占“海外/美元背景”。本土景气和风险偏好用人民银行/统计局/HKMA、利率信用、汇率、融资与行业等相关原始证据补充；**不把美股ETF符号换成A股然后沿用未验证权重**。没有本土数据时说明对本地结论的限制，不能给“完整本土宏观评分”。

## 输出

`02_analysis/macro/macro.md` 分列市场、数据时间、实际来源/备用路径、状态/分量、传导到行业的逻辑、反方信号与复核日。原始JSON仅在脚本真正执行成功后保存并引用。0—100分表示信号强度，不能直接当转变概率，也不能与技术/事件概率平均。
