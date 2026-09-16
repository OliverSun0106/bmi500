# BMI 500 Homework 3 提交清单

当前状态：编程与 profiling 产物已准备；尚未组成完整最终提交。

## 已完成

- [x] OddJobs 登录、计算节点环境配置及通过 Slurm 执行实验。
- [x] `matvec_multiply.py` 实现与输入检查。
- [x] `matvec_test.py`：15 个测试已通过，原测试 starter 改为课件要求的文件名。
- [x] `AI_code_gen.txt`：实际提示摘录、助手信息、过程与验证记录。
- [x] Scanpy 全流程 GNU time、16 个分段计时和最后一步 cProfile。
- [x] 三个成功实验的原始日志、计时、环境及源码快照已下载。
- [x] 分段耗时图、三个 cProfile 图、瓶颈讨论和明确标注的 20K 预测。
- [x] Profiling 专用 `scanpy_profiling.ipynb` 与 `profiling_report/profiling_report.pdf`。

成功实验目录：

| 数据集 | 目录 | 作业编号 |
|---|---|---|
| pbmc3k | `results/pbmc3k-1289747` | 1289747 |
| pbmc6k | `results/pbmc6k-1289760` | 1289760 |
| pbmc10k | `results/pbmc10k-1289774` | 1289774 |

## 需要学生完成或提供

- [ ] Python Quiz：完全由学生独立完成，跳过 Problem 5；不得使用本助手解答、修改或检查答案。
- [ ] `manual_code_review.txt`：真实课堂伙伴的人工 review；不得由 AI 代写或冒充。
- [x] 学生已提供 Claude 审查回复，保存到 `ai_code_review.txt`；模型标识按审查者自述记录，本次 Codex 仅整理文本。
- [ ] 补充实际发送给 Claude 的完整提示；当前 AI review 交互记录仍缺少这一项。
- [ ] 阅读 profiling 报告，确认理解测量与外推的区别、节点和绑定差异等限制。

## 最终整理与提交

- [ ] 将允许整理的材料合并为最终一份 notebook 和一份 PDF；当前 profiling 文件只覆盖其中一部分。Quiz 内容由学生自行加入，助手不处理其答案。
- [ ] 将 Vec-Mat 实现、测试结果、AI 生成记录和两份真实 review 纳入最终材料。
- [ ] 确认最终文件中的图、路径和附件可访问；当前 profiling notebook 已内嵌五张图。
- [ ] 检查 Git diff，提交所需源码、原始实验记录、文档和最终产物；不要提交 Numba 缓存或大型可再生成 H5AD 文件。
- [ ] Commit 并 push 到 `https://github.com/OliverSun0106/bmi500`。
- [ ] 由学生向 TA 发送仓库链接，并按课程要求提交 notebook 和 PDF。

当前没有执行 commit、push 或向 TA 发送消息。
