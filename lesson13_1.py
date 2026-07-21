import streamlit as st
from google import genai
import pandas as pd
import os
import base64
from datetime import datetime

# ページの基本設定（1度だけ呼び出す）
st.set_page_config(page_title="おにぎりメーカー２", page_icon="🍙", layout="wide")

# カスタムCSSで世界観を演出
st.markdown("""
    <style>
    .stApp { background-color: #fff9f0; }
    .main-title { color: #3e2723; font-family: 'Hiragino Maru Gothic Pro', sans-serif; font-weight: bold; text-align: center; }
    label { font-size: 1.2rem !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🍙おにぎり制作メーカー２</h1>", unsafe_allow_html=True)

# APIキーの取得とエラーチェック
if "GEMINI_API_KEY" not in st.secrets:
    st.error("APIキーが見つかりません。StreamlitのSecrets設定で 'GEMINI_API_KEY' を設定してください。")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.5-flash"  # 安定性の高いモデルに変更

# --- 設定とデータ ---
IMAGE_DIR = "images"
SHAPE_MAP = {"しお": "sio.PNG", "焼き": "yaki.PNG", "ケチャップ": "ketya.PNG", "枝豆": "edamame.PNG", "ゆかり": "yukari.PNG"}
FILLING_MAP = {"うめ": "ume.PNG", "さけ": "sake.PNG", "こんぶ": "konnbu.PNG", "明太子": "menntaiko.PNG", "ツナマヨ": "tunamayo.PNG", "えび天": "ebitenn.PNG", "チーズ": "tiizu.PNG"}
GARNISH_MAP = {"のり１": "nori_1.PNG", "たまご": "tamago.PNG", "葉１": "ha_1.PNG", "のり２": "nori_2.PNG", "葉２": "ha_2.PNG"}

# セッション状態の初期化
if 'onigiri_archive' not in st.session_state:
    st.session_state['onigiri_archive'] = []
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = None

@st.cache_data
def get_image_base64(path):
    if not path or not os.path.exists(path): return ""
    with open(path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

def render_onigiri_canvas(shape_key, filling_key, garnish_key, bg_color, size=300):
    s_path = os.path.join(IMAGE_DIR, "onigiri", SHAPE_MAP.get(shape_key, ""))
    f_path = os.path.join(IMAGE_DIR, "guzai", FILLING_MAP.get(filling_key, ""))
    g_path = os.path.join(IMAGE_DIR, "kazari", GARNISH_MAP.get(garnish_key, ""))
    
    s_b64, f_b64, g_b64 = get_image_base64(s_path), get_image_base64(f_path), get_image_base64(g_path)
    
    return f"""
    <div style="position: relative; width: {size}px; height: {size}px; background-color: {bg_color}; border-radius: 50%; overflow: hidden; margin: auto; border: 5px solid #3e2723;">
        {f'<img src="{s_b64}" style="position: absolute; width: 100%;">' if s_b64 else ''}
        {f'<img src="{f_b64}" style="position: absolute; width: 100%; z-index: 2;">' if f_b64 else ''}
        {f'<img src="{g_b64}" style="position: absolute; width: 100%; z-index: 3;">' if g_b64 else ''}
    </div>
    """

def get_ai_evaluation(data):
    """Geminiによるおにぎりの鑑定"""
    prompt = f"""
    あなたはおにぎり界の人間国宝「おにぎり仙人」です。
    以下の構成で作られたおにぎりを情熱的に鑑定してください。
    - ベース: {data['shape']}
    - 具材: {data['filling']}
    - 飾り: {data['garnish']}
    - 作品名: {data['title']}
    1. このおにぎりに「二つ名（例：暁の塩結び）」を付けてください。
    2. 美味しさの評価と、食べるとどうなるかを100文字以内で語ってください。
    """
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return response.text
    except Exception as e:
        return f"鑑定に失敗しました。時間をおいて再度お試しください。(Error: {e})"

# --- UI レイアウト ---
tab1, tab2 = st.tabs(["🍱 おにぎりを作る",  "📜 アーカイブ"])

with tab1:
    col_in, col_pre = st.columns([1, 1])
    with col_in:
        st.subheader("＜デザイン設計＞")
        shape = st.selectbox("ベースを選ぶ", list(SHAPE_MAP.keys()))
        filling = st.radio("中身（具材）", list(FILLING_MAP.keys()), horizontal=True)
        garnish = st.selectbox("外側の飾り", list(GARNISH_MAP.keys()))
        color = st.color_picker("カードの色", "#F0F2F6")
        title = st.text_input("作品名", "今日の一膳")
        
        if st.button("おにぎり完成！", type="primary", use_container_width=True):
            new_entry = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "shape": shape, "filling": filling, "garnish": garnish, "color": color
            }
            with st.spinner("おにぎり仙人が鑑定中..."):
                evaluation = get_ai_evaluation(new_entry)
                new_entry["evaluation"] = evaluation
                st.session_state['onigiri_archive'].insert(0, new_entry)
            st.balloons()
            st.success("アーカイブに保存しました！")
            st.info(evaluation)

    with col_pre:
        st.subheader("＜プレビュー＞")
        st.markdown(render_onigiri_canvas(shape, filling, garnish, color, size=450), unsafe_allow_html=True)

with tab2:
    st.subheader("📜 アーカイブ")
    if not st.session_state['onigiri_archive']:
        st.write("まだおにぎりが握られていません。")
    else:
        for entry in st.session_state['onigiri_archive']:
            with st.expander(f"✨ {entry['date']} : {entry['title']}"):
                col_a, col_b = st.columns([1, 2])
                with col_a:
                    st.markdown(render_onigiri_canvas(entry['shape'], entry['filling'], entry['garnish'], entry['color'], size=250), unsafe_allow_html=True)
                with col_b:
                    st.write(f"**構成:** {entry['shape']} / {entry['filling']} / {entry['garnish']}")
                    st.markdown(f"**仙人の鑑定:**\n\n{entry.get('evaluation', '（鑑定なし）')}")
            
st.sidebar.markdown("---")
st.sidebar.write("© 2025 おにぎり制作メーカー２")
