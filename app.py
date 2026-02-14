import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import time

# --- ページ設定 ---
st.set_page_config(page_title="株主優待AI", page_icon="📈")

# --- APIキー読み込み ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ APIキーが設定されていません。")
    st.stop()

genai.configure(api_key=api_key.strip())

def get_stock_data(code):
    """
    Yahoo!ファイナンスから「メイン情報」と「優待情報」の両方を取得
    東証(.T)だけでなく、札証(.S)なども自動で探す
    """
    # 探す市場の順番（東京 -> 札幌 -> 名古屋 -> 福岡）
    suffixes = ['.T', '.S', '.N', '.Q']
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }

    found_data = None

    for suffix in suffixes:
        stock_id = f"{code}{suffix}"
        url_main = f"https://finance.yahoo.co.jp/quote/{stock_id}"
        url_incentive = f"https://finance.yahoo.co.jp/quote/{stock_id}/incentive"

        try:
            # 1. まずメインページが存在するか確認
            res_main = requests.get(url_main, headers=headers, timeout=5)
            if res_main.status_code == 404:
                continue # なければ次の市場へ (.T -> .S)
            res_main.raise_for_status()

            # 2. 存在したら優待ページも取りに行く
            res_incentive = requests.get(url_incentive, headers=headers, timeout=5)
            
            # HTML解析
            soup_main = BeautifulSoup(res_main.text, 'html.parser')
            soup_incentive = BeautifulSoup(res_incentive.text, 'html.parser')

            # テキスト抽出（AIに読ませる用）
            text_main = soup_main.get_text(separator="\n", strip=True)[:10000]
            text_incentive = soup_incentive.get_text(separator="\n", strip=True)[:10000]

            # 2つの情報を合体
            found_data = f"""
            【情報ソース1：メイン株価ページ（社名・株価・配当情報）】
            {text_main}
            
            --------------------------------
            
            【情報ソース2：株主優待ページ（優待の詳細条件）】
            {text_incentive}
            """
            break # 見つかったらループ終了
            
        except Exception as e:
            continue

    return found_data

def analyze_with_ai(text, code):
    """Gemini Flash Latest で解析"""
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    あなたは凄腕の投資アシスタントです。
    提供されたテキストデータ（Yahoo!ファイナンスの株価ページと優待ページ）から情報を抽出し、
    スマホで見やすいレポートを作成してください。

    【抽出データ】
    1. **会社名**: 正式名称
    2. **現在株価**: 金額と、前日比（+〇円 / +〇% など）
    3. **配当情報**: 1株配当（予想）、配当利回り（予想）
    4. **権利確定月**: 配当と優待それぞれの確定月
    5. **株主優待**: 内容、条件（〇株以上など）、金額換算など具体的に

    【出力フォーマット（マークダウン）】
    ## 🏢 (会社名を入れる) ({code})
    
    ### 📈 株価データ
    - **現在値**: (株価) (前日比)
    - **配当利回り**: (利回り)
    - **1株配当**: (配当金)
    
    ### 🎁 株主優待
    (優待内容を箇条書きで分かりやすく。金額換算できるものは金額も書く)

    ### 📅 権利確定月
    - **配当**: (月)
    - **優待**: (月)

    ---
    ※データが見つからない項目は「情報なし」と記載。
    ※RIZAPのように「配当なし」の場合は正直に書いてください。
    
    解析対象データ:
    {text}
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- アプリ画面 ---
st.title("📈 株主優待＆株価AI")
st.caption("東証・札証・名証・福証すべて対応版")

code = st.text_input("銘柄コード（例: 2928, 7203）", max_chars=4)

if st.button("調べる 🔍", type="primary"):
    if not code.isdigit():
        st.warning("数字4桁で入力してください")
    else:
        with st.spinner(f"全市場から {code} を検索中..."):
            # 1. データ取得（.T .S .N .Q を巡回）
            combined_text = get_stock_data(code)
            
            if combined_text:
                try:
                    # 2. AI解析
                    result = analyze_with_ai(combined_text, code)
                    st.markdown(result)
                    st.success("取得成功！")
                except Exception as e:
                    st.error(f"AI解析エラー: {e}")
            else:
                st.error(f"銘柄コード {code} は見つかりませんでした。上場廃止かコード間違いの可能性があります。")
