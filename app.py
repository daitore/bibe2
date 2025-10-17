import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import MealDatabase

# ページ設定
st.set_page_config(
    page_title="食事バランスナビ",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# データベース初期化
@st.cache_resource
def get_database():
    return MealDatabase()


db = get_database()

# サイドバーメニュー
st.sidebar.markdown("# 🍽️ 食事バランスナビ")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "メニュー",
    [
        "📊 ダッシュボード",
        "➕ 食事記録",
        "📝 記録一覧",
        "📈 統計・グラフ",
        "🍎 食品マスター管理",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ アプリについて")
st.sidebar.info("毎日の食事を記録して、カロリーや栄養バランスを管理しましょう！")

# ===== ダッシュボード =====
if menu == "📊 ダッシュボード":
    st.markdown(
        '<div class="main-header">📊 ダッシュボード</div>', unsafe_allow_html=True
    )

    today = datetime.now().strftime("%Y-%m-%d")

    # 今日のサマリー
    st.subheader("📅 今日の食事サマリー")
    today_summary = db.get_daily_summary(today)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("カロリー", f"{today_summary['calories']:.0f} kcal")
    with col2:
        st.metric("タンパク質", f"{today_summary['protein']:.1f} g")
    with col3:
        st.metric("脂質", f"{today_summary['fat']:.1f} g")
    with col4:
        st.metric("炭水化物", f"{today_summary['carbs']:.1f} g")
    with col5:
        st.metric("食物繊維", f"{today_summary['fiber']:.1f} g")

    st.markdown("---")

    # 今日の食事記録
    st.subheader("🍽️ 今日の食事記録")
    today_meals = db.get_meals_by_date(today)

    if not today_meals.empty:
        display_df = today_meals[
            ["meal_type", "food_name", "amount", "calories", "protein", "fat", "carbs"]
        ].copy()
        display_df.columns = [
            "食事区分",
            "食品名",
            "量(g)",
            "カロリー",
            "タンパク質",
            "脂質",
            "炭水化物",
        ]
        st.dataframe(display_df, use_container_width=True)

        # 栄養バランスの円グラフ
        if (
            today_summary["protein"] > 0
            or today_summary["fat"] > 0
            or today_summary["carbs"] > 0
        ):
            st.subheader("🥧 今日の栄養バランス")
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["タンパク質", "脂質", "炭水化物"],
                        values=[
                            today_summary["protein"] * 4,  # 1gあたり4kcal
                            today_summary["fat"] * 9,  # 1gあたり9kcal
                            today_summary["carbs"] * 4,  # 1gあたり4kcal
                        ],
                        hole=0.3,
                        marker_colors=["#66BB6A", "#FFA726", "#42A5F5"],
                    )
                ]
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "今日の食事記録はまだありません。「➕ 食事記録」から記録を追加してください。"
        )

    # 週間トレンド
    st.markdown("---")
    st.subheader("📈 直近7日間のカロリー推移")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=6)

    weekly_data = db.get_period_summary(
        start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )

    if not weekly_data.empty:
        fig = px.line(
            weekly_data,
            x="date",
            y="total_calories",
            labels={"date": "日付", "total_calories": "カロリー (kcal)"},
            markers=True,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("直近7日間のデータがありません。")

# ===== 食事記録 =====
elif menu == "➕ 食事記録":
    st.markdown('<div class="main-header">➕ 食事記録</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        date = st.date_input("日付", datetime.now())
        meal_type = st.selectbox("食事区分", ["朝食", "昼食", "夕食", "間食"])

    with col2:
        # 食品マスターから選択
        foods = db.get_all_foods()
        if foods:
            food_names = [f["name"] for f in foods]
            selected_food = st.selectbox("食品を選択", [""] + food_names)

            if selected_food:
                food_data = next((f for f in foods if f["name"] == selected_food), None)
                if food_data:
                    amount = st.number_input(
                        "量 (g)", min_value=0.0, value=100.0, step=10.0
                    )

                    # 栄養素を自動計算（100gあたりの値を基準に）
                    ratio = amount / 100.0
                    calc_calories = food_data["calories"] * ratio
                    calc_protein = food_data["protein"] * ratio
                    calc_fat = food_data["fat"] * ratio
                    calc_carbs = food_data["carbs"] * ratio
                    calc_fiber = food_data["fiber"] * ratio

                    st.info(
                        f"""
                    **計算された栄養素 ({amount}g分)**
                    - カロリー: {calc_calories:.1f} kcal
                    - タンパク質: {calc_protein:.1f} g
                    - 脂質: {calc_fat:.1f} g
                    - 炭水化物: {calc_carbs:.1f} g
                    - 食物繊維: {calc_fiber:.1f} g
                    """
                    )

                    if st.button("記録を追加", type="primary"):
                        db.add_meal_record(
                            date=date.strftime("%Y-%m-%d"),
                            meal_type=meal_type,
                            food_name=selected_food,
                            amount=amount,
                            calories=calc_calories,
                            protein=calc_protein,
                            fat=calc_fat,
                            carbs=calc_carbs,
                            fiber=calc_fiber,
                        )
                        st.success(f"✅ {selected_food}を記録しました！")
                        st.rerun()
        else:
            st.warning(
                "食品マスターにデータがありません。初期化スクリプトを実行してください。"
            )

# ===== 記録一覧 =====
elif menu == "📝 記録一覧":
    st.markdown('<div class="main-header">📝 記録一覧</div>', unsafe_allow_html=True)

    # 日付範囲選択
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("終了日", datetime.now())

    # データ取得
    meals = db.get_meals_by_date_range(
        start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )

    if not meals.empty:
        st.info(f"📊 {len(meals)}件の記録が見つかりました")

        # 表示用のデータフレーム
        display_df = meals[
            [
                "id",
                "date",
                "meal_type",
                "food_name",
                "amount",
                "calories",
                "protein",
                "fat",
                "carbs",
                "fiber",
            ]
        ].copy()
        display_df.columns = [
            "ID",
            "日付",
            "食事区分",
            "食品名",
            "量(g)",
            "カロリー",
            "タンパク質",
            "脂質",
            "炭水化物",
            "食物繊維",
        ]

        st.dataframe(display_df, use_container_width=True)

        # 削除機能
        st.markdown("---")
        st.subheader("🗑️ 記録の削除")

        record_id = st.number_input("削除するレコードのID", min_value=1, step=1)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("削除", type="secondary"):
                try:
                    db.delete_meal_record(record_id)
                    st.success(f"✅ ID {record_id} の記録を削除しました")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")
    else:
        st.info("指定期間のデータがありません。")

# ===== 統計・グラフ =====
elif menu == "📈 統計・グラフ":
    st.markdown(
        '<div class="main-header">📈 統計・グラフ</div>', unsafe_allow_html=True
    )

    # 期間選択
    period_type = st.radio("表示期間", ["日別", "週別", "月別"], horizontal=True)

    if period_type == "日別":
        selected_date = st.date_input("日付を選択", datetime.now())
        date_str = selected_date.strftime("%Y-%m-%d")

        summary = db.get_daily_summary(date_str)

        st.subheader(f"📅 {date_str} の栄養サマリー")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("カロリー", f"{summary['calories']:.0f} kcal")
        with col2:
            st.metric("タンパク質", f"{summary['protein']:.1f} g")
        with col3:
            st.metric("脂質", f"{summary['fat']:.1f} g")
        with col4:
            st.metric("炭水化物", f"{summary['carbs']:.1f} g")
        with col5:
            st.metric("食物繊維", f"{summary['fiber']:.1f} g")

        # 食事区分ごとの内訳
        meals = db.get_meals_by_date(date_str)
        if not meals.empty:
            meal_summary = meals.groupby("meal_type")["calories"].sum().reset_index()

            fig = px.bar(
                meal_summary,
                x="meal_type",
                y="calories",
                labels={"meal_type": "食事区分", "calories": "カロリー (kcal)"},
                color="meal_type",
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    elif period_type == "週別":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)

        st.subheader(
            f"📅 {start_date.strftime('%Y-%m-%d')} 〜 {end_date.strftime('%Y-%m-%d')}"
        )

        weekly_data = db.get_period_summary(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

        if not weekly_data.empty:
            # カロリーグラフ
            fig1 = px.line(
                weekly_data,
                x="date",
                y="total_calories",
                labels={"date": "日付", "total_calories": "カロリー (kcal)"},
                markers=True,
                title="カロリー推移",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 栄養素の推移
            fig2 = go.Figure()
            fig2.add_trace(
                go.Scatter(
                    x=weekly_data["date"],
                    y=weekly_data["total_protein"],
                    mode="lines+markers",
                    name="タンパク質",
                )
            )
            fig2.add_trace(
                go.Scatter(
                    x=weekly_data["date"],
                    y=weekly_data["total_fat"],
                    mode="lines+markers",
                    name="脂質",
                )
            )
            fig2.add_trace(
                go.Scatter(
                    x=weekly_data["date"],
                    y=weekly_data["total_carbs"],
                    mode="lines+markers",
                    name="炭水化物",
                )
            )
            fig2.update_layout(
                title="栄養素の推移",
                xaxis_title="日付",
                yaxis_title="量 (g)",
                height=400,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # 平均値
            st.subheader("📊 週間平均")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "平均カロリー", f"{weekly_data['total_calories'].mean():.0f} kcal"
                )
            with col2:
                st.metric(
                    "平均タンパク質", f"{weekly_data['total_protein'].mean():.1f} g"
                )
            with col3:
                st.metric("平均脂質", f"{weekly_data['total_fat'].mean():.1f} g")
            with col4:
                st.metric("平均炭水化物", f"{weekly_data['total_carbs'].mean():.1f} g")
        else:
            st.info("この期間のデータがありません。")

    else:  # 月別
        year_month = st.date_input("年月を選択", datetime.now())

        # その月の開始日と終了日を計算
        start_date = year_month.replace(day=1)
        if start_date.month == 12:
            end_date = start_date.replace(
                year=start_date.year + 1, month=1, day=1
            ) - timedelta(days=1)
        else:
            end_date = start_date.replace(
                month=start_date.month + 1, day=1
            ) - timedelta(days=1)

        st.subheader(f"📅 {start_date.strftime('%Y年%m月')}")

        monthly_data = db.get_period_summary(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

        if not monthly_data.empty:
            # カロリーグラフ
            fig1 = px.bar(
                monthly_data,
                x="date",
                y="total_calories",
                labels={"date": "日付", "total_calories": "カロリー (kcal)"},
                title="日別カロリー",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 月間サマリー
            st.subheader("📊 月間サマリー")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "合計カロリー", f"{monthly_data['total_calories'].sum():.0f} kcal"
                )
                st.metric(
                    "平均カロリー", f"{monthly_data['total_calories'].mean():.0f} kcal"
                )
            with col2:
                st.metric(
                    "合計タンパク質", f"{monthly_data['total_protein'].sum():.1f} g"
                )
                st.metric(
                    "平均タンパク質", f"{monthly_data['total_protein'].mean():.1f} g"
                )
            with col3:
                st.metric("合計炭水化物", f"{monthly_data['total_carbs'].sum():.1f} g")
                st.metric("平均炭水化物", f"{monthly_data['total_carbs'].mean():.1f} g")
        else:
            st.info("この期間のデータがありません。")

# ===== 食品マスター管理 =====
elif menu == "🍎 食品マスター管理":
    st.markdown(
        '<div class="main-header">🍎 食品マスター管理</div>', unsafe_allow_html=True
    )

    st.subheader("登録済み食品一覧")

    foods = db.get_all_foods()

    if foods:
        df = pd.DataFrame(foods)
        df.columns = [
            "ID",
            "食品名",
            "カロリー",
            "タンパク質",
            "脂質",
            "炭水化物",
            "食物繊維",
        ]
        st.dataframe(df, use_container_width=True)

        st.info(f"📊 合計 {len(foods)} 種類の食品が登録されています")
    else:
        st.warning("食品マスターにデータがありません。")

    st.markdown("---")
    st.subheader("新しい食品を追加")

    with st.form("add_food_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_food_name = st.text_input("食品名")
            new_calories = st.number_input(
                "カロリー (100gあたり)", min_value=0.0, value=0.0
            )
            new_protein = st.number_input(
                "タンパク質 (100gあたり)", min_value=0.0, value=0.0
            )

        with col2:
            new_fat = st.number_input("脂質 (100gあたり)", min_value=0.0, value=0.0)
            new_carbs = st.number_input(
                "炭水化物 (100gあたり)", min_value=0.0, value=0.0
            )
            new_fiber = st.number_input(
                "食物繊維 (100gあたり)", min_value=0.0, value=0.0
            )

        submitted = st.form_submit_button("追加", type="primary")

        if submitted and new_food_name:
            db.add_food_to_master(
                new_food_name, new_calories, new_protein, new_fat, new_carbs, new_fiber
            )
            st.success(f"✅ {new_food_name}を追加しました！")
            st.rerun()
        elif submitted:
            st.error("食品名を入力してください。")
