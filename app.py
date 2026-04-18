import streamlit as st
import pandas as pd
import json
from datetime import date
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ITEMS_FILE = DATA_DIR / "items.json"
RECORDS_FILE = DATA_DIR / "records.json"

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def get_items():
    return load_json(ITEMS_FILE, [])

def save_items(items):
    save_json(ITEMS_FILE, items)

def get_records():
    return load_json(RECORDS_FILE, [])

def save_records(records):
    save_json(RECORDS_FILE, records)

if not get_items():
    demo = [
        {"id":1,"name":"そば粉","category":"粉類","unit":"kg","price":800,"min_stock":5},
        {"id":2,"name":"小麦粉","category":"粉類","unit":"kg","price":300,"min_stock":3},
        {"id":3,"name":"カレールー","category":"調味料","unit":"箱","price":500,"min_stock":10},
        {"id":4,"name":"醤油","category":"調味料","unit":"本","price":1000,"min_stock":3},
        {"id":5,"name":"みりん","category":"調味料","unit":"本","price":800,"min_stock":2},
        {"id":6,"name":"鶏肉","category":"肉類","unit":"kg","price":1200,"min_stock":5},
        {"id":7,"name":"豚肉","category":"肉類","unit":"kg","price":1500,"min_stock":3},
        {"id":8,"name":"玉ねぎ","category":"野菜","unit":"個","price":50,"min_stock":20},
        {"id":9,"name":"長ネギ","category":"野菜","unit":"本","price":100,"min_stock":15},
        {"id":10,"name":"卵","category":"卵乳","unit":"パック","price":300,"min_stock":5},
        {"id":11,"name":"めんつゆ","category":"調味料","unit":"本","price":600,"min_stock":5},
        {"id":12,"name":"サラダ油","category":"調味料","unit":"本","price":400,"min_stock":3},
    ]
    save_items(demo)

STORES = ["セントラルキッチン"] + [f"店舗{i}" for i in range(1,16)]
st.set_page_config(page_title="棚卸しくん", page_icon="📦", layout="wide")
st.sidebar.title("📦 棚卸しくん")
mode = st.sidebar.radio("モード", ["棚卸し入力","本部ダッシュボード","商品マスタ管理"])

if mode == "棚卸し入力":
    st.title("📱 棚卸し入力")
    store = st.selectbox("店舗を選択", STORES)
    count_date = st.date_input("棚卸し日", value=date.today())
    date_str = count_date.strftime("%Y-%m-%d")
    st.divider()
    items = get_items()
    categories = sorted(set(item["category"] for item in items))
    records = get_records()
    prev = {}
    store_records = [r for r in records if r["store"] == store]
    if store_records:
        latest_date = max(r["date"] for r in store_records)
        for r in store_records:
            if r["date"] == latest_date:
                prev[r["item_id"]] = {"unopened": r.get("unopened",0), "opened_pct": r.get("opened_pct",0)}
    tabs = st.tabs(categories)
    input_data = {}
    for tab, cat in zip(tabs, categories):
        with tab:
            cat_items = [item for item in items if item["category"] == cat]
            for item in cat_items:
                st.markdown(f"**{item['name']}** ({item['unit']} / 単価¥{item['price']:,})")
                prev_vals = prev.get(item["id"], {"unopened":0,"opened_pct":0})
                col1, col2 = st.columns(2)
                with col1:
                    unopened = st.number_input("未開封",min_value=0.0,step=1.0,value=float(prev_vals["unopened"]),key=f"u_{item['id']}")
                with col2:
                    opened_pct = st.select_slider("開封済み残量",options=[0,10,20,30,40,50,60,70,80,90],value=int(prev_vals["opened_pct"]),key=f"o_{item['id']}",format_func=lambda x: f"{x}%" if x > 0 else "なし")
                total_qty = unopened + (opened_pct / 100)
                st.caption(f"合計: {total_qty:.1f} {item['unit']}  金額: ¥{total_qty * item['price']:,.0f}")
                input_data[item["id"]] = {"unopened":unopened,"opened_pct":opened_pct,"total_qty":total_qty}
                st.markdown("---")
    if st.button("保存する", type="primary", use_container_width=True):
        records = [r for r in get_records() if not (r["store"]==store and r["date"]==date_str)]
        for item in items:
            d = input_data.get(item["id"],{"unopened":0,"opened_pct":0,"total_qty":0})
            records.append({"store":store,"date":date_str,"item_id":item["id"],"item_name":item["name"],"category":item["category"],"unit":item["unit"],"price":item["price"],"unopened":d["unopened"],"opened_pct":d["opened_pct"],"total_qty":d["total_qty"],"subtotal":d["total_qty"]*item["price"]})
        save_records(records)
        st.success(f"{store}({date_str})を保存しました!")
        st.balloons()

elif mode == "本部ダッシュボード":
    st.title("📊 本部ダッシュボード")
    records = get_records()
    if not records:
        st.info("棚卸しデータがありません。")
        st.stop()
    df = pd.DataFrame(records)
    dates = sorted(df["date"].unique(), reverse=True)
    selected_date = st.selectbox("棚卸し日", dates)
    day_df = df[df["date"] == selected_date]
    col1, col2 = st.columns(2)
    col1.metric("全店在庫総額", f"¥{day_df['subtotal'].sum():,.0f}")
    col2.metric("入力済み店舗", f"{day_df['store'].nunique()} / {len(STORES)}")
    st.subheader("店舗別")
    ss = day_df.groupby("store")["subtotal"].sum().reset_index()
    ss.columns = ["店舗","在庫金額"]
    st.dataframe(ss, use_container_width=True, hide_index=True)
    not_submitted = [s for s in STORES if s not in set(day_df["store"].unique())]
    if not_submitted:
        st.warning(f"未入力: {', '.join(not_submitted)}")
    st.subheader("カテゴリ別")
    st.bar_chart(day_df.groupby("category")["subtotal"].sum())
    st.subheader("CSVエクスポート")
    csv = day_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSVダウンロード",csv,f"棚卸し_{selected_date}.csv","text/csv",use_container_width=True)

elif mode == "商品マスタ管理":
    st.title("⚙️ 商品マスタ管理")
    items = get_items()
    if items:
        st.dataframe(pd.DataFrame(items)[["name","category","unit","price","min_stock"]].rename(columns={"name":"商品名","category":"カテゴリ","unit":"単位","price":"単価","min_stock":"最低在庫"}),use_container_width=True,hide_index=True)
    st.divider()
    st.subheader("商品追加")
    with st.form("add"):
        name = st.text_input("商品名")
        cats = sorted(set(item["category"] for item in items)) if items else []
        cat_opt = st.selectbox("カテゴリ", cats + ["新しいカテゴリ"])
        new_cat = st.text_input("新カテゴリ名") if cat_opt == "新しいカテゴリ" else ""
        c1,c2,c3 = st.columns(3)
        unit = c1.text_input("単位",value="個")
        price = c2.number_input("単価",min_value=0,step=10)
        min_stock = c3.number_input("最低在庫",min_value=0.0,step=1.0)
        if st.form_submit_button("追加",type="primary",use_container_width=True):
            if name.strip():
                category = new_cat.strip() if cat_opt == "新しいカテゴリ" else cat_opt
                new_id = max((i["id"] for i in items),default=0) + 1
                items.append({"id":new_id,"name":name.strip(),"category":category,"unit":unit,"price":price,"min_stock":min_stock})
                save_items(items)
                st.success(f"{name} を追加しました!")
                st.rerun()
