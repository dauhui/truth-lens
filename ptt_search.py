import requests
from bs4 import BeautifulSoup

def search_ptt(keyword, board="MobileComm", max_articles=3):
    # PTT 的搜尋網址格式
    url = f"https://www.ptt.cc/bbs/{board}/search?q={keyword}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    cookies = {'over18': '1'}

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
    except Exception as e:
        print(f"搜尋失敗: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 抓取搜尋結果列表
    articles = []
    # 找到所有標題區塊 (r-ent)
    links = soup.find_all('div', class_='r-ent')
    
    print(f"在 {board} 版搜尋 '{keyword}'，找到 {len(links)} 篇結果...")

    for link in links:
        if len(articles) >= max_articles:
            break
            
        title_tag = link.find('div', class_='title').find('a')
        
        if title_tag:
            title = title_tag.text.strip()
            # 排除公告或已被刪除的文章
            if "公告" in title or "刪除" in title:
                continue
                
            article_url = "https://www.ptt.cc" + title_tag['href']
            
            # 這裡我們順便抓一下推文數，當作「熱度」參考
            nrec_tag = link.find('div', class_='nrec')
            nrec = nrec_tag.text.strip() if nrec_tag else "0"
            
            articles.append({
                'title': title,
                'url': article_url,
                'score': nrec
            })

    return articles

# --- 測試 ---
if __name__ == "__main__":
    # 你可以把關鍵字改成你想買的東西，例如 "Pixel 9" 或 "Sony 耳機"
    results = search_ptt("Pixel 9", board="MobileComm")
    
    for i, res in enumerate(results):
        print(f"{i+1}. [{res['score']}] {res['title']}")
        print(f"   Link: {res['url']}")