# 物流销售数据分析

这是一个面向初学者的物流销售数据分析项目，使用 Python、pandas 和 Matplotlib 完成数据清洗、异常值识别、配送时效分析、销售金额汇总和图表展示。

## 项目内容

- 删除完全重复行、空值行和无关字段，并重新生成连续索引。
- 将“元/万元”等混乱的销售金额转换为人民币元数值。
- 标准化销售时间，并提取“月份”列。
- 识别销售金额最小值为 0、数量或金额标准差过大的异常情况。
- 按月份、销售区域、货品，以及“货品 + 销售区域”组合分析按时交货率。
- 使用两个柱状图比较不同区域和不同货品的销售金额贡献。

## 目录说明

| 文件或目录 | 作用 |
| --- | --- |
| `物流销售数据分析.ipynb` | 带有逐行中文注释的交互式分析 Notebook |
| `analysis.py` | 可复用的数据清洗、指标计算和图表生成代码 |
| `完整维度分析.md` | 四个分析维度的思路和代码说明 |
| `weidu.md` | 月份、销售区域等维度分析说明 |
| `异常值识别说明.md` | 异常值识别规则说明 |
| `月份列添加说明.md` | 月份列生成过程说明 |
| `tests/` | 自动化测试和测试报告 |
| `figures/` | 运行分析后生成的图表 |
| `data_wuliu_cleaned.csv` | 清洗后的明细数据 |
| `kpis.csv` | 核心指标结果 |
| `quality_report.csv` | 数据质量报告 |

## 环境安装

建议使用 Python 3.10 或更高版本。在项目目录中执行：

```bash
python -m venv .venv
```

Windows PowerShell 激活虚拟环境：

```powershell
.venv\\Scripts\\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 运行分析脚本

原始数据默认读取 `E:\\animal\\data_wuliu.csv`。如果路径不同，请修改 `analysis.py` 中的 `DEFAULT_SOURCE`，然后执行：

```bash
python analysis.py
```

脚本会生成清洗数据、核心指标、质量报告和分析图表。

## 运行 Notebook

1. 启动 Jupyter Notebook：

   ```bash
   jupyter notebook
   ```

2. 打开 `物流销售数据分析.ipynb`。
3. 建议选择“从头运行全部单元格”。
4. 先运行数据读取和清洗单元，再运行汇总表和绘图单元。

## 运行测试

```bash
python -m pytest tests/ -v --tb=short
```

测试覆盖金额解析、重复数据清洗、字段类型、真实 CSV 冒烟检查和核心指标计算。

## 数据安全说明

项目只包含示例数据分析代码和结果，不应在代码或 Notebook 中保存 API key、密码、Token 等敏感信息。运行前请确认本地数据文件不包含需要保护的个人或业务隐私。

