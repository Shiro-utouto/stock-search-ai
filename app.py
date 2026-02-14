import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="株主優待AI", page_icon="🎁")

# --- 1. APIキーの確認と設定 ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ APIキーが設定されていません。Secretsを確認してください。")
    st.stop()

# 余計なスペースが入っているとエラーになるので削除する処理
genai.configure(api_key=api_key.strip())

# --- 2. 診断モード（サイドバー） ---
st.sidebar.header("🔧 診断メニュー")
if st.sidebar.button("接続テストを実行"):
    try:
        st.sidebar.info("AIに接続中...")
        # 使えるモデルの一覧を取得してみる
        models = [m.name for m in genai.list_models()]
        st.sidebar.success("✅ 接続成功！")
        st.sidebar.write("使えるモデル:", models)
    except Exception as e:
        st.sidebar.error(f"❌ 接続失敗: {e}")
        st.sidebar.warning("APIキーが間違っているか、有効になっていない可能性があります。")

# --- 3. メイン機能 ---
def get_stock_data(code):
    url = f"https://finance.yahoo.co.jp/quote/{code}.T/incentive"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.get_text(separator="\n", strip=True)[:15000]
    except Exception as e:
        return None

def analyze_with_ai(text, code):
    # 最新のモデル名を指定
    target_model = 'gemini-1.5-flash'
    model = genai.GenerativeModel(target_model)
    
    prompt = f"""
    銘柄コード「{code}」の株主優待情報です。以下をまとめてください。
    1. 配当金と利回り
    2. 権利確定月
    3. 優待内容（具体的に）
    
    データ: {text}
    """
    response = model.generate_content(prompt)
    return response.text

st.title("🎁 株主優待＆配当AI")
code = st.text_input("銘柄コード（例: 7203）", max_chars=4)

if st.button("調べる 🔍"):
    if not code.isdigit():
        st.warning("数字4桁で入力してください")
    else:
        with st.spinner(f"{code} を検索中..."):
            raw_text = get_stock_data(code)
            if raw_text:
                try:
                    result = analyze_with_ai(raw_text, code)
                    st.markdown("### 📊 分析結果")
                    st.write(result)
                except Exception as e:
                    st.error(f"AIエラー: {e}")
                    st.info("👈 左上の「>」を押してサイドバーを開き、「接続テスト」を試してください。")
            else:
                st.error("データが取得できませんでした。コードを確認してください。")
