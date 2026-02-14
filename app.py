import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# --- ページ設定 ---
st.set_page_config(page_title="株主優待AI", page_icon="🎁")

# --- APIキー読み込み ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key.strip())

def get_stock_data(code):
    """Yahoo!ファイナンスから情報を取得"""
    url = f"https://finance.yahoo.co.jp/quote/{code}.T/incentive"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        # 余計な空白を削除してテキスト化
        return soup.get_text(separator="\n", strip=True)[:15000]
    except Exception as e:
        return None

def analyze_with_ai(text, code):
    """Gemini Flash Latest で解析"""
    # ★あなたのリストのNo.16にあった、一番安全なモデル名を使います
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    あなたは投資アシスタントです。
    以下のテキストは銘柄コード「{code}」のYahoo!ファイナンス（株主優待ページ）の情報です。
    ここから重要な情報を抽出し、スマホで見やすいようにマークダウン形式で整理してください。

    【出力フォーマット】
    ## 🏢 {code} の優待情報
    
    ### 💰 配当・権利日
    - **予想配当**: (ここに入れる)
    - **配当利回り**: (ここに入れる)
    - **権利確定月**: (ここに入れる)
    
    ### 🎁 株主優待の内容
    (ここに具体的な優待内容、条件、金額などを箇条書きで分かりやすく要約する)

    ### 📅 優待の権利確定月
    (ここに入れる)

    ---
    ※情報が見つからない項目は「記載なし」としてください。
    
    解析対象データ:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- アプリ画面 ---
st.title("🎁 株主優待＆配当AI")
st.caption("AI (Flash Latest) が詳細を調べます")

code = st.text_input("銘柄コード（例: 7203）", max_chars=4)

if st.button("調べる 🔍", type="primary"):
    if not code.isdigit():
        st.warning("数字4桁で入力してください")
    else:
        with st.spinner(f"コード {code} をAIが解析中..."):
            # 1. データ取得
            raw_text = get_stock_data(code)
            
            if raw_text:
                try:
                    # 2. AI解析
                    result = analyze_with_ai(raw_text, code)
                    st.markdown(result)
                    st.success("解析完了！")
                except Exception as e:
                    # エラー内容を詳しく表示
                    st.error(f"エラーが発生しました: {e}")
                    st.write("もしQuotaエラーが出る場合は、しばらく時間をおいて試してください。")
            else:
                st.error("データの取得に失敗しました。コードが正しいか確認してください。")
