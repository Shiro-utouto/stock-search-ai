import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os

# --- 設定: ページタイトルなど ---
st.set_page_config(page_title="株主優待AI", page_icon="🎁")

# --- APIキーの読み込み (StreamlitのSecrets機能を使う) ---
# ※ローカルで動かす場合はここに直接 api_key="AIza..." と書いても動きますが、
# 公開時はSecretsを使うのが安全です。
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("APIキーが設定されていません。StreamlitのSecretsに設定してください。")

def get_stock_data(code):
    """Yahoo!ファイナンスから株主優待ページのHTMLを取得"""
    url = f"https://finance.yahoo.co.jp/quote/{code}.T/incentive"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ページ全体のテキストを取得（余計な空白削除）
        text = soup.get_text(separator="\n", strip=True)
        # AIに渡すデータ量を制限（多すぎるとエラーになることがあるため）
        return text[:20000] 
    except Exception as e:
        return None

def analyze_with_ai(text, code):
    """Gemini AIで情報を抽出・整理"""
    model = genai.GenerativeModel('gemini-1.5-flash') # 無料枠で高速なモデル
    
    prompt = f"""
    あなたはプロの投資家アシスタントです。
    以下のテキストは、銘柄コード「{code}」のYahoo!ファイナンス（株主優待ページ）のデータです。
    このデータから、以下の4点を抽出し、スマホで見やすい形式でまとめてください。
    
    【抽出してほしい項目】
    1. **配当金（予想）** と **配当利回り**
    2. **配当の権利確定月**
    3. **株主優待の内容**（条件や内容を簡潔に要約。QUOカードや自社商品など具体的に）
    4. **優待の権利確定月**

    もし情報が見つからない場合は「情報なし」としてください。
    
    --- データ ---
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- アプリの画面構成 ---
st.title("🎁 株主優待＆配当AI")
st.caption("銘柄コードを入れるとAIが詳細を調べます")

code = st.text_input("銘柄コード（例: 7203）", max_chars=4)

if st.button("調べる 🔍"):
    if not code.isdigit():
        st.warning("数字4桁で入力してください")
    else:
        with st.spinner(f"{code} の情報を収集中..."):
            # 1. データ取得
            raw_text = get_stock_data(code)
            
            if raw_text:
                # 2. AI解析
                st.info("AIが解析しています...")
                result = analyze_with_ai(raw_text, code)
                
                # 3. 結果表示
                st.markdown("### 📊 分析結果")
                st.write(result)
                st.success("完了しました！")
            else:
                st.error("データの取得に失敗しました。コードが正しいか確認してください。")
