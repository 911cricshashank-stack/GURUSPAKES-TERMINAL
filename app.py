import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re

# 1. PAGE SETUP
st.set_page_config(page_title="GuruSpakes Live Market News", layout="wide")

# 2. THE MASTER CSS
st.markdown("""
<style>
    .stApp { 
        background: radial-gradient(circle at top, #1a1f24 0%, #050505 100%); 
        padding-bottom: 60px;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    /* Custom Logo Typography */
    .logo-container {
        display: flex; align-items: center; justify-content: center; gap: 20px; margin-top: 10px; margin-bottom: 0px;
    }
    .logo-left { text-align: right; line-height: 0.9; }
    .logo-guru { color: #FFFFFF; font-size: 1.4rem; font-family: Arial, sans-serif; letter-spacing: 1px; }
    .logo-finance { color: #FFD700; font-size: 3.5rem; font-weight: bold; font-family: 'Times New Roman', Times, serif; text-shadow: 0px 2px 10px rgba(255, 215, 0, 0.2); }
    .logo-divider { border-left: 2px solid #333; height: 50px; }
    .logo-names { text-align: left; line-height: 1.4; font-family: 'Times New Roman', Times, serif; font-size: 1.1rem; color: #E0E0E0;}
    
    .terminal-title {
        text-align: center; color: #FFD700; font-family: 'Times New Roman', Times, serif; 
        letter-spacing: 4px; font-size: 1.4rem; margin-top: 15px; margin-bottom: 15px;
    }

    /* THE NEW LEAD CAPTURE BUTTON */
    .lead-btn-container {
        text-align: center;
        margin-bottom: 30px;
    }
    .lead-btn {
        background-color: #FFD700;
        color: #000000 !important;
        padding: 12px 35px;
        font-size: 1.1rem;
        font-weight: bold;
        font-family: Arial, sans-serif;
        text-decoration: none;
        border-radius: 4px;
        box-shadow: 0px 4px 15px rgba(255, 215, 0, 0.3);
        transition: 0.3s;
        display: inline-block;
        letter-spacing: 1px;
    }
    .lead-btn:hover {
        background-color: #FFFFFF;
        box-shadow: 0px 6px 20px rgba(255, 255, 255, 0.5);
        text-decoration: none;
        transform: translateY(-2px);
    }

    /* Scrollable Glass Boxes */
    .news-container {
        background-color: rgba(15, 20, 25, 0.6); border: 1px solid rgba(255, 215, 0, 0.2); 
        border-radius: 8px; padding: 20px; height: 380px;
        overflow-y: auto; box-shadow: 0px 10px 30px rgba(0,0,0,0.8); margin-bottom: 20px;
    }
    .news-container::-webkit-scrollbar { width: 6px; }
    .news-container::-webkit-scrollbar-track { background: #0a0a0a; border-radius: 10px; }
    .news-container::-webkit-scrollbar-thumb { background: #FFD700; border-radius: 10px; }

    /* News Articles */
    .news-item { margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid rgba(255, 215, 0, 0.1); }
    .news-date { color: #888888; font-size: 0.8em; margin-bottom: 4px; font-family: monospace; }
    .news-link { color: #E0E0E0 !important; text-decoration: none; font-size: 1.05em; line-height: 1.4; display: block; transition: 0.2s; }
    .news-link:hover { color: #FFD700 !important; }
    
    /* Column Headers with inline logos */
    .column-header {
        text-align: center; color: #FFD700; font-family: 'Times New Roman', Times, serif;
        letter-spacing: 2px; margin-bottom: 10px; font-size: 1.3rem;
        border-bottom: 1px solid rgba(255, 215, 0, 0.3); padding-bottom: 10px;
        display: flex; align-items: center; justify-content: center; gap: 10px;
    }
    .col-logo { height: 22px; width: 22px; border-radius: 4px; background: white; padding: 2px;}

    /* Live Ticker Bar */
    .ticker-bar {
        background-color: #050505; color: #FFF; padding: 10px 20px; border-top: 1px solid #FFD700;
        font-size: 1rem; font-family: monospace; position: fixed; bottom: 0; left: 0; width: 100%;
        z-index: 100; display: flex; justify-content: space-between;
    }
</style>
""", unsafe_allow_html=True)

# 3. RENDER THE CUSTOM GURUSPAKES HEADER & CTA BUTTON
st.markdown("""
<div class="logo-container">
    <div class="logo-left">
        <span class="logo-guru">Guru Spakes</span><br>
        <span class="logo-finance">Finance</span>
    </div>
    <div class="logo-divider"></div>
    <div class="logo-names">
        Chaitanya Sabharwal<br>
        Shashank Jha
    </div>
</div>
<div class="terminal-title">LIVE MARKET NEWS</div>

<div class="lead-btn-container">
    <a href="https://www.guruspakes.com/about-us" target="_blank" class="lead-btn">
        💼 BOOK A FREE PORTFOLIO REVIEW
    </a>
</div>
""", unsafe_allow_html=True)

# 4. FILTERS ROW
f_col1, f_col2 = st.columns(2)
with f_col1:
    search_query = st.text_input("🔍 Search Keyword:", placeholder="e.g. Reliance, RBI, Budget...")
with f_col2:
    sector_filter = st.selectbox("📂 Filter By Sector:", ["All Sectors", "Banking & Finance", "IT & Tech", "Auto", "Energy & Oil", "Pharma"])
st.write("<br>", unsafe_allow_html=True)

# 5. DATA SOURCES 
FEEDS = {
    "Mint": "https://www.livemint.com/rss/markets",
    "Moneycontrol": "https://news.google.com/rss/search?q=site:moneycontrol.com+when:1d&hl=en-IN&gl=IN&ceid=IN:en", 
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "MarketWatch": "https://news.google.com/rss/search?q=site:marketwatch.com+when:1d&hl=en-US&gl=US&ceid=US:en"
}

LOGOS = {
    "Mint": "https://www.google.com/s2/favicons?domain=livemint.com&sz=128",
    "Moneycontrol": "https://www.google.com/s2/favicons?domain=moneycontrol.com&sz=128",
    "Economic Times": "https://www.google.com/s2/favicons?domain=economictimes.indiatimes.com&sz=128",
    "CNBC": "https://www.google.com/s2/favicons?domain=cnbc.com&sz=128",
    "MarketWatch": "https://www.google.com/s2/favicons?domain=marketwatch.com&sz=128"
}

# 6. THE STEALTH DATA FETCHER
@st.cache_data(ttl=1800)
def get_news(url):
    news_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.content, 'xml')
        now_ts = datetime.now(timezone.utc).timestamp() 
        
        for item in soup.find_all('item'): 
            title = item.title.get_text(strip=True) if item.title else ""
            if " - Moneycontrol" in title:
                title = title.replace(" - Moneycontrol", "")
            if " - MarketWatch" in title:
                title = title.replace(" - MarketWatch", "")
                
            link = item.link.get_text(strip=True) if item.link else ""
            pub_date = item.pubDate.get_text(strip=True) if item.pubDate else ""
            
            short_date = "NEW"
            if pub_date:
                try:
                    dt = parsedate_to_datetime(pub_date)
                    dt_ts = dt.timestamp()
                    if (now_ts - dt_ts) > 172800: # 48 hours
                        continue
                    short_date = dt.strftime("%d %b").upper()
                except:
                    pass 
            
            if title and link:
                news_list.append({"Headline": title, "Link": link, "Date": short_date})
                
            if len(news_list) >= 25:
                break
    except Exception:
        pass
    return news_list

# STRICT REGEX FILTER
def filter_news(news_data, query, sector):
    filtered = news_data
    if query:
        filtered = [article for article in filtered if query.lower() in article['Headline'].lower()]
        
    if sector != "All Sectors":
        keywords = {
            "Banking & Finance": [r"\bbank\b", r"\bbanks\b", r"\brbi\b", r"\bhdfc\b", r"\bsbi\b", r"\bicici\b", r"\bkotak\b", r"\baxis\b", r"\bfinance\b", r"\bloan\b", r"\bloans\b", r"\brate\b", r"\brates\b"],
            "IT & Tech": [r"\btech\b", r"\bit\b", r"\binfosys\b", r"\btcs\b", r"\bwipro\b", r"\bhcl\b", r"\bai\b", r"\bsoftware\b", r"\bapple\b", r"\bnvidia\b"],
            "Auto": [r"\bauto\b", r"\bautos\b", r"\bautomobile\b", r"\bautomobiles\b", r"\btata motors\b", r"\bmahindra\b", r"\bmaruti\b", r"\bev\b", r"\bevs\b", r"\bvehicle\b", r"\bvehicles\b", r"\bbajaj\b", r"\bhero\b", r"\btvs\b"],
            "Energy & Oil": [r"\boil\b", r"\benergy\b", r"\breliance\b", r"\bpower\b", r"\bsolar\b", r"\bcoal\b", r"\bcrude\b", r"\bgas\b", r"\bongc\b", r"\bntpc\b"],
            "Pharma": [r"\bpharma\b", r"\bhealth\b", r"\bsun pharma\b", r"\bcipla\b", r"\bdr reddy\b", r"\blupin\b", r"\bfda\b", r"\bhospital\b"]
        }
        
        sector_patterns = keywords.get(sector, [])
        if sector_patterns:
            combined_pattern = re.compile("|".join(sector_patterns), re.IGNORECASE)
            filtered = [article for article in filtered if combined_pattern.search(article['Headline'])]
            
    return filtered

# 7. HTML COLUMN BUILDER
def build_column(title, logo_url, news_data):
    html = f'''
    <div class="column-header">
        <img src="{logo_url}" class="col-logo"> {title}
    </div>
    <div class="news-container">
    '''
    if not news_data:
        html += '<div class="news-item"><div class="news-link" style="color:#888;">No recent news found matching the criteria.</div></div>'
    for article in news_data:
        html += f'<div class="news-item"><div class="news-date">[{article["Date"]}]</div><a href="{article["Link"]}" target="_blank" class="news-link">{article["Headline"]} ↗</a></div>'
    html += '</div>'
    return html

# 8. RENDER ROW 1: INDIAN MARKETS
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(build_column("MINT", LOGOS["Mint"], filter_news(get_news(FEEDS["Mint"]), search_query, sector_filter)), unsafe_allow_html=True)
with col2:
    st.markdown(build_column("MONEYCONTROL", LOGOS["Moneycontrol"], filter_news(get_news(FEEDS["Moneycontrol"]), search_query, sector_filter)), unsafe_allow_html=True)
with col3:
    st.markdown(build_column("ECONOMIC TIMES", LOGOS["Economic Times"], filter_news(get_news(FEEDS["Economic Times"]), search_query, sector_filter)), unsafe_allow_html=True)

# 9. RENDER ROW 2: GLOBAL MARKETS
st.markdown("<h4 style='text-align: center; color: #E0E0E0; font-family: Times New Roman; margin-top: 10px; margin-bottom: 15px; letter-spacing: 2px;'>🌍 GLOBAL MARKETS</h4>", unsafe_allow_html=True)
g_col1, g_col2 = st.columns(2)
with g_col1:
    st.markdown(build_column("CNBC INT.", LOGOS["CNBC"], filter_news(get_news(FEEDS["CNBC"]), search_query, sector_filter)), unsafe_allow_html=True)
with g_col2:
    st.markdown(build_column("MARKETWATCH", LOGOS["MarketWatch"], filter_news(get_news(FEEDS["MarketWatch"]), search_query, sector_filter)), unsafe_allow_html=True)

# 10. LIVE TICKER
@st.cache_data(ttl=300) 
def get_ticker_prices():
    prices_html = ""
    try:
        indices = {"SENSEX": "^BSESN", "NIFTY": "^NSEI", "BANK NIFTY": "^NSEBANK"}
        for name, symbol in indices.items():
            try:
                tkr = yf.Ticker(symbol)
                hist = tkr.history(period="5d")
                if len(hist) >= 2:
                    prev = hist['Close'].iloc[-2]
                    current = hist['Close'].iloc[-1]
                    change_pct = ((current - prev) / prev) * 100
                    color = "#00FF00" if change_pct >= 0 else "#FF4136" 
                    sign = "+" if change_pct >= 0 else ""
                    prices_html += f"<span style='margin-right: 25px;'>{name} <span style='color:{color};'>{sign}{change_pct:.2f}%</span></span>"
            except: continue
    except: pass
    return prices_html

current_time = datetime.now().strftime("%I:%M:%S %p IST | %b %d, %Y").upper()
prices = get_ticker_prices()

ticker_html = f"<div class='ticker-bar'><div>{prices}</div><div><span style='color: #00FF00;'>🟢 LIVE</span> &nbsp;&nbsp; {current_time}</div></div>"
st.markdown(ticker_html, unsafe_allow_html=True)