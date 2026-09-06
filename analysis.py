"""物流销售数据清洗、指标计算与可视化。

这个文件把 Notebook 中反复使用的步骤整理成可复用函数，方便直接运行：
读取原始 CSV → 清洗字段 → 计算指标 → 保存结果和图表。
"""
from __future__ import annotations
from pathlib import Path
import re
import matplotlib.pyplot as plt
import pandas as pd

# 默认的原始数据位置。运行时也可以通过函数参数传入其他文件。
DEFAULT_SOURCE = Path(r"E:\animal\data_wuliu.csv")
# 默认把结果保存到当前脚本所在目录，避免覆盖原始数据。
DEFAULT_OUTPUT = Path(__file__).resolve().parent

# 原始中文列名与程序内部统一使用的英文列名的对应关系。
RAW_TO_STANDARD = {
    "订单号": "order_id",
    "订单行": "order_line",
    "销售时间": "sale_date",
    "交货时间": "delivery_date",
    "货品交货状况": "delivery_status",
    "货品": "product",
    "货品用户反馈": "customer_feedback",
    "销售区域": "sales_region",
    "数量": "quantity",
    "销售金额": "sales_amount_cny",
}
# 数据中可能出现的同义列名，先改成标准中文列名再继续处理。
RAW_COLUMN_ALIASES = {"货品交货状态": "货品交货状况"}
# 清洗后必须保留的基础字段顺序。
STANDARD_COLUMNS = list(RAW_TO_STANDARD.values())

def parse_amount(value: object) -> float:
    """把“1052,75元”或“11,50万元”转换为人民币元数值。"""
    # 空值没有可转换的金额，用 NaN 表示“缺失”。
    if pd.isna(value):
        return float("nan")

    # 去掉首尾空格和数字中间可能出现的普通空格。
    text = str(value).strip().replace(" ", "")
    # 只接受“数字 + 元/万元”的格式，其他内容视为格式异常。
    match = re.fullmatch(r"([0-9]+(?:,[0-9]+)?)\s*(元|万元)", text)
    if not match:
        return float("nan")

    # 原始数据用逗号表示小数；万元需要乘以 10000 统一为元。
    return float(match.group(1).replace(",", ".")) * (10000 if match.group(2) == "万元" else 1)

def _add_flag(flags: pd.Series, condition: pd.Series, label: str) -> pd.Series:
    """把满足条件的行追加一个质量问题标签。"""
    # 条件中的缺失值不应被当作 True，否则会误标数据质量问题。
    condition = condition.fillna(False)
    # 第一条问题直接替换“正常”，后续问题用分号连接起来。
    return flags.where(~condition, flags.where(flags.eq("正常"), flags + ";") + label)

def _iqr_mask(series: pd.Series) -> pd.Series:
    """使用 IQR 规则标记统计离群值，但不删除这些记录。"""
    # 先转成数值；无法转换的内容会变成缺失值。
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    # 没有有效数据时，无法计算四分位数，因此全部返回 False。
    if valid.empty:
        return pd.Series(False, index=series.index)

    # 计算中间 50% 数据的范围，作为判断极端值的基准。
    q1, q3 = valid.quantile([0.25, 0.75]); iqr = q3 - q1
    # 所有值相同（IQR 为 0）时，不把任何值判为离群。
    if iqr == 0:
        return pd.Series(False, index=series.index)

    # 超过上下边界 1.5 倍 IQR 的值会被标记。
    return (numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)

def load_and_clean(source: str | Path = DEFAULT_SOURCE) -> tuple[pd.DataFrame, dict]:
    """读取原始 CSV，完成清洗并返回明细数据和质量摘要。"""
    source = Path(source)
    # 原始文件使用 GB18030 编码；先全部按字符串读取，避免过早类型推断。
    raw = pd.read_csv(source, encoding="gb18030", dtype="string")

    # 在清洗前记录基线，便于后续报告“删了多少重复、原始缺失多少”。
    raw_rows = len(raw)
    raw_duplicates = int(raw.duplicated().sum())
    raw_missing = raw.isna().sum().to_dict()

    # 兼容“货品交货状态”和“货品交货状况”两种列名写法。
    raw = raw.rename(columns=RAW_COLUMN_ALIASES)
    # 将中文列名统一成程序内部的标准英文列名。
    df = raw.rename(columns=RAW_TO_STANDARD).copy()

    # 完全重复的记录只保留第一次出现的那一条。
    df = df.drop_duplicates(keep="first").reset_index(drop=True)

    # 文本字段去掉首尾空格；空字符串统一成缺失值，避免分类时产生脏类别。
    text_columns = ["order_id", "delivery_status", "product", "customer_feedback", "sales_region"]
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip().replace("", pd.NA)

    # 数值字段转换失败时保留为缺失，而不是猜测填补。
    df["order_line"] = pd.to_numeric(df["order_line"], errors="coerce").astype("Int64")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Float64")

    # 日期转换失败的内容会变成 NaT，后面会被质量标记捕获。
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["delivery_date"] = pd.to_datetime(df["delivery_date"], errors="coerce")

    # 金额统一换算为人民币元，并使用可空浮点类型保存缺失值。
    df["sales_amount_cny"] = df["sales_amount_cny"].map(parse_amount).astype("Float64")

    # 缺失交货状态显示为“未知”，但后面 is_on_time 仍会保留缺失含义。
    df["delivery_status"] = df["delivery_status"].fillna("未知")

    # 交货天数 = 交货日期 - 销售日期。
    df["delivery_days"] = (df["delivery_date"] - df["sale_date"]).dt.days.astype("Int64")
    # 只有明确写着“按时交货”才算 True；“未知”不参与按时率计算。
    df["is_on_time"] = df["delivery_status"].eq("按时交货").astype("boolean")
    df.loc[df["delivery_status"].eq("未知"), "is_on_time"] = pd.NA

    # 默认每行状态为“正常”，再逐条追加发现的问题。
    flags = pd.Series("正常", index=df.index, dtype="string")
    flags = _add_flag(flags, df["order_id"].isna(), "订单号缺失")
    flags = _add_flag(flags, df["quantity"].isna(), "数量缺失或无效")
    flags = _add_flag(flags, df["sales_amount_cny"].isna(), "金额缺失或格式异常")
    flags = _add_flag(flags, df["sale_date"].isna() | df["delivery_date"].isna(), "日期缺失或格式异常")
    flags = _add_flag(flags, df["delivery_days"].lt(0), "交货日期早于销售日期")
    flags = _add_flag(flags, df["quantity"].le(0), "数量非正")
    flags = _add_flag(flags, df["sales_amount_cny"].le(0), "金额非正")
    flags = _add_flag(flags, _iqr_mask(df["quantity"]), "数量统计离群")
    flags = _add_flag(flags, _iqr_mask(df["sales_amount_cny"]), "金额统计离群")
    # 保存质量标签；一行可能同时存在多个问题。
    df["data_quality_flag"] = flags
    # 按产品文档规定的顺序输出字段。
    df = df[STANDARD_COLUMNS + ["delivery_days", "is_on_time", "data_quality_flag"]]

    # 汇总清洗前后行数、缺失值和质量标签，供质量报告使用。
    quality = {"source_file": str(source), "raw_rows": raw_rows, "clean_rows": len(df), "duplicate_rows_removed": raw_duplicates, "raw_missing": raw_missing, "clean_missing": df.isna().sum().to_dict(), "quality_flag_counts": df["data_quality_flag"].value_counts().to_dict()}
    return df, quality

def make_kpis(df: pd.DataFrame) -> pd.Series:
    """根据清洗后的明细数据计算核心经营指标。"""
    # nunique 不统计缺失订单号；按时率的分母会自动排除未知状态。
    return pd.Series({"清洗后记录数":len(df),"订单数":df["order_id"].nunique(dropna=True),"销售数量合计":df["quantity"].sum(min_count=1),"销售金额合计（元）":df["sales_amount_cny"].sum(min_count=1),"平均交货天数":df["delivery_days"].mean(),"按时交货率":df["is_on_time"].mean()})

def save_figures(df: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """生成并保存月度、区域、交货和用户反馈分析图。"""
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    # 设置中文字体候选，避免图表标题和坐标轴出现乱码。
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]; plt.rcParams["axes.unicode_minus"] = False
    paths = []

    # 按销售月份汇总金额和数量，用于观察趋势。
    monthly = df.assign(month=df["sale_date"].dt.to_period("M")).groupby("month", observed=True).agg(sales_amount_cny=("sales_amount_cny","sum"), quantity=("quantity","sum"))
    fig, ax = plt.subplots(figsize=(10,5)); monthly["sales_amount_cny"].plot(ax=ax, marker="o", color="#1f77b4"); ax.set(title="月度销售金额趋势", xlabel="销售月份", ylabel="销售金额（元）"); ax.grid(alpha=.25); fig.tight_layout(); p=output_dir/"01_月度销售金额趋势.png"; fig.savefig(p,dpi=150); plt.close(fig); paths.append(p)
    # 比较各销售区域的销售金额，并按金额从高到低排列。
    region = df.groupby("sales_region", dropna=False, observed=True)["sales_amount_cny"].sum().sort_values(ascending=False); ax=region.plot(kind="bar",figsize=(9,5),color="#2ca02c",title="销售区域销售金额"); ax.set(xlabel="销售区域",ylabel="销售金额（元）"); ax.grid(axis="y",alpha=.25); fig=ax.get_figure(); fig.tight_layout(); p=output_dir/"02_区域销售金额.png"; fig.savefig(p,dpi=150); plt.close(fig); paths.append(p)
    # 统计每种交货状态的记录数，使用饼图展示占比。
    status=df["delivery_status"].value_counts(dropna=False); ax=status.plot(kind="pie",autopct="%.1f%%",figsize=(7,7),title="交货状态分布"); ax.set_ylabel(""); fig=ax.get_figure(); fig.tight_layout(); p=output_dir/"03_交货状态分布.png"; fig.savefig(p,dpi=150); plt.close(fig); paths.append(p)
    # 交货天数直方图可以帮助观察交付周期集中在哪些区间。
    ax=df["delivery_days"].dropna().plot(kind="hist",bins=12,figsize=(9,5),color="#ff7f0e",title="交货天数分布"); ax.set(xlabel="交货天数",ylabel="记录数"); ax.grid(axis="y",alpha=.25); fig=ax.get_figure(); fig.tight_layout(); p=output_dir/"04_交货天数分布.png"; fig.savefig(p,dpi=150); plt.close(fig); paths.append(p)
    # 统计用户反馈类别，查看不同反馈的数量差异。
    feedback=df["customer_feedback"].value_counts(dropna=False); ax=feedback.plot(kind="bar",figsize=(8,5),color="#9467bd",title="用户反馈分布"); ax.set(xlabel="用户反馈",ylabel="记录数"); ax.grid(axis="y",alpha=.25); fig=ax.get_figure(); fig.tight_layout(); p=output_dir/"05_用户反馈分布.png"; fig.savefig(p,dpi=150); plt.close(fig); paths.append(p)
    return paths

def run_pipeline(source: str | Path = DEFAULT_SOURCE, output_dir: str | Path = DEFAULT_OUTPUT) -> tuple[pd.DataFrame, dict]:
    """一键执行清洗、指标导出、质量报告和图表生成。"""
    # 统一创建输出目录，然后依次保存明细、指标、质量报告和图片。
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True); df,quality=load_and_clean(source); df.to_csv(output_dir/"data_wuliu_cleaned.csv",index=False,encoding="utf-8-sig"); make_kpis(df).rename("value").to_csv(output_dir/"kpis.csv",encoding="utf-8-sig"); pd.DataFrame({"metric":list(quality["clean_missing"]),"missing_count":list(quality["clean_missing"].values())}).to_csv(output_dir/"quality_report.csv",index=False,encoding="utf-8-sig"); save_figures(df,output_dir/"figures"); return df,quality

if __name__ == "__main__":
    # 直接运行 python analysis.py 时，使用默认路径执行完整流程。
    result,summary=run_pipeline(); print(make_kpis(result).to_string()); print(f"已输出 {len(result)} 条清洗记录；删除重复记录 {summary['duplicate_rows_removed']} 条。")
