from pathlib import Path
import pandas as pd
from analysis import load_and_clean, make_kpis, parse_amount

def test_parse_amount_supports_units_and_decimal_comma():
    assert parse_amount("1052,75元") == 1052.75
    assert parse_amount("11,50万元") == 115000
    assert pd.isna(parse_amount("无法识别"))

def test_cleaning_normalizes_spaces_duplicates_and_types(tmp_path):
    source=tmp_path/"sample.csv"; header="订单号,订单行,销售时间,交货时间,货品交货状态,货品,货品用户反馈,销售区域,数量,销售金额"; row='P1,10,2016-7-30,2016-9-30, 按时交货,货品1,质量合格,华北,2,"1052,75元"'; source.write_text(header+"\n"+row+"\n"+row,encoding="gb18030")
    df,quality=load_and_clean(source)
    assert len(df)==1; assert df.loc[0,"delivery_status"]=="按时交货"; assert df.loc[0,"sales_amount_cny"]==1052.75; assert str(df["sale_date"].dtype).startswith("datetime"); assert quality["duplicate_rows_removed"]==1

def test_real_csv_smoke():
    source=Path(r"E:\animal\data_wuliu.csv")
    if not source.exists(): return
    df,quality=load_and_clean(source); assert quality["raw_rows"]==1161; assert quality["duplicate_rows_removed"]==9; assert len(df)==1152; assert {"delivery_days","is_on_time","data_quality_flag"}.issubset(df.columns); assert df["sales_amount_cny"].notna().all()

def test_kpis_are_computable():
    df=pd.DataFrame({"order_id":["P1","P2"],"quantity":[2.,3.],"sales_amount_cny":[10.,20.],"delivery_days":[60,61],"is_on_time":pd.Series([True,False],dtype="boolean")}); kpis=make_kpis(df); assert kpis["订单数"]==2; assert kpis["销售数量合计"]==5; assert kpis["销售金额合计（元）"]==30; assert kpis["按时交货率"]==.5
