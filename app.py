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
    return load_json(ITEMS_FILE, DEFAULT_ITEMS)

def get_records():
    return load_json(RECORDS_FILE, [])

# === 信濃路 店舗一覧 ===
STORES = [
    "セントラルキッチン",
    "キーノ和歌山市駅店",
    "日赤和歌山医療センター店",
    "かつらぎ店",
    "海南店",
    "岩出バイパス店",
    "国体道路店",
    "四ヶ郷店",
    "鳴神店",
    "ダイワロイネット和歌山店",
    "しなの路 打田店",
]

# === 商品マスタ（そば・うどん業態） ===
DEFAULT_ITEMS = [
    {"id":"M001","name":"そば粉","category":"麺類原材料","unit":"kg","price":800,"min_stock":10},
    {"id":"M002","name":"うどん粉（中力粉）","category":"麺類原材料","unit":"kg","price":300,"min_stock":20},
    {"id":"M003","name":"生そば（冷凍）","category":"麺類原材料","unit":"食","price":120,"min_stock":50},
    {"id":"M004","name":"生うどん（冷凍）","category":"麺類原材料","unit":"食","price":100,"min_stock":50},
    {"id":"S001","name":"かつおだし（業務用）","category":"つゆ・調味料","unit":"L","price":600,"min_stock":10},
    {"id":"S002","name":"濃縮つゆ","category":"つゆ・調味料","unit":"L","price":450,"min_stock":15},
    {"id":"S003","name":"みりん","category":"つゆ・調味料","unit":"L","price":350,"min_stock":5},
    {"id":"S004","name":"醤油（業務用）","category":"つゆ・調味料","unit":"L","price":400,"min_stock":10},
    {"id":"S005","name":"カレールー（業務用）","category":"つゆ・調味料","unit":"kg","price":700,"min_stock":5},
    {"id":"T001","name":"天ぷら油","category":"天ぷら材料","unit":"L","price":350,"min_stock":10},
    {"id":"T002","name":"天ぷら粉","category":"天ぷら材料","unit":"kg","price":250,"min_stock":10},
    {"id":"T003","name":"エビ（冷凍）","category":"天ぷら材料","unit":"kg","price":2500,"min_stock":5},
    {"id":"T004","name":"さつまいも","category":"天ぷら材料","unit":"kg","price":300,"min_stock":5},
    {"id":"T005","name":"ちくわ","category":"天ぷら材料","unit":"本","price":30,"min_stock":50},
    {"id":"P001","name":"ネギ","category":"トッピング","unit":"kg","price":400,"min_stock":5},
    {"id":"P002","name":"天かす","category":"トッピング","unit":"kg","price":350,"min_stock":5},
    {"id":"P003","name":"かまぼこ","category":"トッピング","unit":"本","price":200,"min_stock":20},
    {"id":"P004","name":"わかめ（乾燥）","category":"トッピング","unit":"kg","price":1800,"min_stock":2},
    {"id":"P005","name":"油揚げ","category":"トッピング","unit":"枚","price":25,"min_stock":50},
    {"id":"P006","name":"鶏肉（もも）","category":"トッピング","unit":"kg","price":900,"min_stock":5},
    {"id":"C001","name":"割り箸","category":"消耗品","unit":"膳","price":3,"min_stock":500},
    {"id":"C002","name":"持ち帰り容器","category":"消耗品","unit":"個","price":25,"min_stock":200},
    {"id":"C003","name":"ナプキン","category":"消耗品","unit":"枚","price":2,"min_stock":500},
]

st.set_page_config(page_title="信濃路 棚卸し管理", page_icon="🍜", layout="wide")

mode = st.sidebar.selectbox("メニュー", ["棚卸し入力", "本部ダッシュボード", "商品マスタ管理"])

# ==========================================
# 棚卸し入力
# ==========================================
if mode == "棚卸し入力":
    st.title("🍜 信濃路 棚卸し入力")
    store = st.selectbox("店舗を選択", STORES)
    inv_date = st.date_input("棚卸し日", value=date.today())
    items = get_items()
    categories = sorted(set(i["category"] for i in items))
    cat_filter = st.selectbox("カテゴリ", ["すべて"] + categories)
    filtered = items if cat_filter == "すべて" else [i for i in items if i["category"] == cat_filter]

    st.caption("未開封数と開封済み残量（%）を入力してください")
    entries = []
    for item in filtered:
        with st.container():
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"**{item['name']}**（{item['unit']}・¥{item['price']:,}）")
            unopened = cols[1].number_input("未開封", min_value=0, value=0, key=f"u_{item['id']}")
            opened_pct = cols[2].number_input("開封残%", min_value=0, max_value=100, value=0, step=10, key=f"o_{item['id']}")
            total_qty = unopened + opened_pct / 100
            subtotal = total_qty * item["price"]
            cols[3].markdown(f"計 **{total_qty:.1f}** {item['unit']}<br>¥{subtotal:,.0f}", unsafe_allow_html=True)
            entries.append({
                "store": store, "date": str(inv_date), "item_id": item["id"],
                "item_name": item["name"], "category": item["category"],
                "unit": item["unit"], "price": item["price"],
                "unopened": unopened, "opened_pct": opened_pct,
                "total_qty": round(total_qty, 2), "subtotal": round(subtotal)
            })

    if st.button("💾 保存する", type="primary", use_container_width=True):
        records = get_records()
        records = [r for r in records if not (r["store"] == store and r["date"] == str(inv_date))]
        records.extend([e for e in entries if e["total_qty"] > 0])
        save_json(RECORDS_FILE, records)
        st.success(f"✅ {store}の棚卸しデータを保存しました！")
        st.rerun()

# ==========================================
# 本部ダッシュボード
# ==========================================
elif mode == "本部ダッシュボード":
    st.title("📊 信濃路 本部ダッシュボード")
    records = get_records()
    if not records:
        st.info("棚卸しデータがありません。")
        st.stop()
    df = pd.DataFrame(records)
    dates = sorted(df["date"].unique(), reverse=True)
    selected_date = st.selectbox("棚卸し日", dates)
    day_df = df[df["date"] == selected_date]

    total_value = day_df["subtotal"].sum()
    store_count = day_df["store"].nunique()
    item_count = day_df["item_name"].nunique()
    avg_per_store = total_value / store_count if store_count > 0 else 0

    st.markdown("### 📈 全体サマリー")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 全店在庫総額", f"¥{total_value:,.0f}")
    col2.metric("🏪 入力済み店舗", f"{store_count} / {len(STORES)}")
    col3.metric("📦 品目数", f"{item_count} 品目")
    col4.metric("📊 1店舗平均", f"¥{avg_per_store:,.0f}")

    not_submitted = [s for s in STORES if s not in set(day_df["store"].unique())]
    if not_submitted:
        st.error(f"🚨 未入力店舗: {', '.join(not_submitted)}")
    else:
        st.success("✅ 全店舗入力完了！")

    st.divider()

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 🏪 店舗別在庫金額")
        ss = day_df.groupby("store")["subtotal"].sum().sort_values(ascending=True).reset_index()
        ss.columns = ["店舗", "在庫金額"]
        st.bar_chart(ss.set_index("店舗"), horizontal=True)

    with col_right:
        st.markdown("### 🏷️ カテゴリ別構成")
        cs = day_df.groupby("category")["subtotal"].sum().reset_index()
        cs.columns = ["カテゴリ", "金額"]
        cs["構成比"] = (cs["金額"] / cs["金額"].sum() * 100).round(1)
        for _, row in cs.sort_values("金額", ascending=False).iterrows():
            pct = row["構成比"]
            st.markdown(f"**{row['カテゴリ']}** - ¥{row['金額']:,.0f} ({pct}%)")
            st.progress(pct / 100)

    st.divider()

    st.markdown("### ⚠️ 在庫アラート")
    items_master = get_items()
    min_map = {i["id"]: i["min_stock"] for i in items_master}
    alerts = []
    for _, row in day_df.iterrows():
        ms = min_map.get(row["item_id"], 0)
        if row["total_qty"] <= ms:
            alerts.append({"🏪 店舗": row["store"], "📦 商品": row["item_name"], "📉 現在庫": row["total_qty"], "📏 最低在庫": ms, "単位": row["unit"]})
    if alerts:
        st.dataframe(pd.DataFrame(alerts), use_container_width=True, hide_index=True)
    else:
        st.success("🎉 在庫少の商品はありません！")

    st.divider()

    st.markdown("### 📋 明細データ")
    detail = day_df[["store", "category", "item_name", "unopened", "opened_pct", "total_qty", "price", "subtotal"]].copy()
    detail.columns = ["店舗", "カテゴリ", "商品名", "未開封", "開封残%", "合計数量", "単価", "金額"]
    detail["金額"] = detail["金額"].apply(lambda x: f"¥{x:,.0f}")
    st.dataframe(detail, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 📥 エクスポート")
    csv = day_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 CSVダウンロード", csv, f"棚卸し_{selected_date}.csv", "text/csv", use_container_width=True)

# ==========================================
# 商品マスタ管理
# ==========================================
elif mode == "商品マスタ管理":
    st.title("🏷️ 商品マスタ管理")
    items = get_items()
    st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)

    st.subheader("➕ 商品追加")
    with st.form("add_item"):
        col1, col2 = st.columns(2)
        new_id = col1.text_input("商品ID", value=f"X{len(items)+1:03d}")
        new_name = col2.text_input("商品名")
        col3, col4 = st.columns(2)
        new_cat = col3.selectbox("カテゴリ", ["麺類原材料", "つゆ・調味料", "天ぷら材料", "トッピング", "消耗品"])
        new_unit = col4.text_input("単位", value="kg")
        col5, col6 = st.columns(2)
        new_price = col5.number_input("単価（円）", min_value=0, value=100)
        new_min = col6.number_input("最低在庫数", min_value=0, value=5)
        if st.form_submit_button("追加する"):
            if new_name:
                items.append({"id": new_id, "name": new_name, "category": new_cat, "unit": new_unit, "price": new_price, "min_stock": new_min})
                save_json(ITEMS_FILE, items)
                st.success(f"「{new_name}」を追加しました！")
                st.rerun()
            else:
                st.error("商品名を入力してください。")

st.divider()
st.caption("© 2026 信濃路グループ 棚卸し管理システム")
