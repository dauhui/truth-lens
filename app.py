import streamlit as st
import time
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
import pandas as pd
import altair as alt

# 引入你原本的模組
from ptt_search import search_ptt
from ptt_spider import parse_ptt_article

# 設定頁面資訊
st.set_page_config(page_title="Truth Lens - 真實風向", page_icon="🔍")

# 側邊欄：設定 API Key (這樣你就不用把 Key 寫死在程式碼裡，更安全)
with st.sidebar:
    st.header("⚙️ 設定")

    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # 可以在側邊欄顯示一個提示，讓你知道是用系統 Key
        with st.sidebar:
            st.success("✅ 已載入系統 API Key")
    else:
        with st.sidebar:
            api_key = st.text_input("請輸入 Gemini API Key", type="password")

    board_option = st.selectbox("選擇看板", ["MobileComm", "PC_Shopping", "Lifeismoney", "Gossiping"])
    
    st.markdown("---")
    st.markdown("### 關於 Truth Lens")
    st.caption("利用 AI 分析 PTT 真實評價，過濾業配與水軍。")

# 主畫面
st.title("🔍 Truth Lens 真實風向掃描器")
st.markdown("想買東西怕踩雷？想知道真實災情？讓 AI 幫你讀完 PTT。")

keyword = st.text_input("輸入你想查詢的產品/關鍵字", "iPhone 16")
start_btn = st.button("開始分析", type="primary")

# --- 核心邏輯區 ---
if start_btn:
    if not api_key:
        st.error("請先在左側輸入 Gemini API Key！")
    else:
        genai.configure(api_key=api_key.strip())
        
        # 1. 搜尋
        with st.status("🚀 正在啟動 PTT 爬蟲...", expanded=True) as status:
            st.write(f"正在 {board_option} 版搜尋 '{keyword}'...")
            search_results = search_ptt(keyword, board=board_option, max_articles=5)
            
            if not search_results:
                status.update(label="找不到相關文章", state="error")
                st.error("找不到相關文章，請嘗試更換關鍵字。")
            else:
                st.write(f"找到 {len(search_results)} 篇熱門討論，開始平行爬取...")
                
                # 2. 爬取 (平行處理)
                crawled_data = []
                progress_bar = st.progress(0)
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {executor.submit(parse_ptt_article, res['url']): res for res in search_results}
                    
                    for i, future in enumerate(future_to_url):
                        data = future.result()
                        if data:
                            crawled_data.append(data)
                            st.write(f"✅ 已讀取：{data['meta']['title']}")
                        progress_bar.progress((i + 1) / len(search_results))
                
                status.update(label="爬取完成！正在進行 AI 分析...", state="running", expanded=False)

                # 整理數據
                chart_data = []
                for data in crawled_data:
                    push_count = sum(1 for c in data['comments'] if c['type'] == '推')
                    boo_count = sum(1 for c in data['comments'] if c['type'] == '噓')
                    arrow_count = sum(1 for c in data['comments'] if c['type'] == '→')
                    total_interaction = push_count + boo_count + arrow_count
                    
                    # 計算「推噓比」 (P/B Ratio) 用來判斷是「共識」還是「戰場」
                    # 避免分母為 0
                    if total_interaction == 0:
                        controversy_score = 0
                    else:
                        # 單純用 (推 - 噓) 來做一個簡單的淨指標
                        controversy_score = push_count - boo_count

                    chart_data.append({
                        "文章標題": data['meta']['title'], # 這裡保留完整標題
                        "熱度": total_interaction,
                        "淨推文數": controversy_score,
                        "推": push_count,
                        "噓": boo_count,
                        "連結": data['meta'].get('url', '#')
                    })

                df = pd.DataFrame(chart_data)

                # --- 升級版圖表：Altair 互動式水平圖 ---
                st.subheader("🔥 熱門討論排行")
                st.caption("滑鼠移上去可看詳細數值，顏色越紅代表「噓」越多，越綠代表「推」越多")

                # 定義圖表
                chart = alt.Chart(df).mark_bar().encode(
                    # X軸：顯示「熱度」 (討論總數)，代表這篇有多紅
                    x=alt.X('熱度', title='討論熱度 (留言總數)'),
                    
                    # Y軸：顯示「標題」，設為水平避免被截斷，並依熱度排序
                    y=alt.Y('文章標題', sort='-x', title=None, axis=alt.Axis(labelLimit=300)), 
                    
                    # 顏色：用「淨推文數」來上色。
                    # 綠色(正值) = 大家推 (可能是產品好，或罵得好)
                    # 紅色(負值) = 大家噓 (可能是產品爛到護航不了，或那是業配文)
                    color=alt.Color('淨推文數', scale=alt.Scale(scheme='redyellowgreen'), title='淨推值'),
                    
                    # Tooltip：滑鼠移上去顯示的資訊
                    tooltip=['文章標題', '熱度', '推', '噓', '淨推文數']
                ).properties(
                    height=300 # 設定圖表高度，讓條形不要太肥
                )

                # 顯示圖表
                st.altair_chart(chart, use_container_width=True)

                # 3. AI 分析 (這裡放入你原本的聚合邏輯)
                if crawled_data:
                    # 簡單的聚合 Prompt (你可以把你 main.py 裡那個很棒的 Prompt 複製過來這裡)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    
                    # 組合內容...
                    combined_content = ""
                    for data in crawled_data:
                        combined_content += f"標題：{data['meta']['title']}\n內文摘要：{data['body'][:300]}...\n\n"
                        # 加入一些留言...
                        for c in data['comments'][:10]:
                             combined_content += f"{c['type']}: {c['content']}\n"
                    
                    prompt = f"""
                    你是一個購物決策助手。請針對以下 PTT 關於「{keyword}」的討論資料進行分析。
                    請用 Markdown 格式輸出：
                    1. ## 懶人包結論
                    2. ## 真實優缺點表格
                    3. ## 網友入手機會/價格建議
                    4. ## Truth Score (0-10分)
                    
                    資料：
                    {combined_content}
                    """
                    
                    response = model.generate_content(prompt)
                    
                    # 4. 顯示結果
                    st.divider()
                    st.subheader("📊 AI 分析報告")
                    st.markdown(response.text)
                    
                    # --- 💰 變現區 (導購按鈕) ---
                    st.divider()
                    st.subheader("🛒 哪裡買最划算？")
                    
                    col1, col2 = st.columns(2)
                    
                    # 這裡暫時用假的搜尋連結，之後我們會換成你的 Affiliate Link
                    shopee_url = f"https://shopee.tw/search?keyword={keyword}" 
                    momo_url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={keyword}"
                    
                    with col1:
                        st.link_button(f"前往 🦐 蝦皮比價 ({keyword})", shopee_url, use_container_width=True)
                        st.caption("查看銷量與價格")
                    
                    with col2:
                        st.link_button(f"前往 Ⓜ️ Momo 找現貨", momo_url, use_container_width=True)
                        st.caption("24h 快速到貨")

                    status.update(label="分析完成！", state="complete", expanded=True)
                        
                else:
                    st.error("爬取內容失敗。")