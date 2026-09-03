import streamlit as st
import pandas as pd
import time
import concurrent.futures
import re
import nest_asyncio
from scrapling import StealthyFetcher
import os
# أمر أوتوماتيكي لتثبيت المتصفح الخفي داخل الخادم السحابي
import os
import streamlit as st

@st.cache_resource
def install_browsers():
    # تثبيت المتصفح الخفي مرة واحدة فقط وحفظه في الذاكرة المخبئية
    os.system("playwright install chromium")
    os.system("patchright install chromium")

install_browsers()

def unified_job_scraper(keyword="AI Engineer", location="Egypt"):
    all_jobs = []

    # ---------------------------------------------------------
    # 1. Wuzzuf
    # ---------------------------------------------------------
    wuzzuf_url = f"https://wuzzuf.net/search/jobs/?q={keyword}&filters[post_date][0]=within_24_hours"
    try:
        response_wuzzuf = StealthyFetcher.fetch(wuzzuf_url, headless=True, network_idle=True)
        page_title = response_wuzzuf.css('title')[0].text if response_wuzzuf.css('title') else "Unknown"
        st.info(f"🔍 [Debug] Wuzzuf Page Title: {page_title}")
        
        w_jobs = response_wuzzuf.css('div.css-pkv5jc, div.css-1gatmva')
        w_jobs = response_wuzzuf.css('div.css-pkv5jc, div.css-1gatmva')
        
        for job in w_jobs:
            title_nodes = job.css('h2 a') or job.css('h2')
            title = title_nodes[0].text.strip() if title_nodes else "N/A"
            
            link = "N/A"
            if title_nodes:
                raw_link = "N/A"
                if hasattr(title_nodes[0], 'attrib'):
                    raw_link = title_nodes[0].attrib.get('href', 'N/A')
                elif hasattr(title_nodes[0], 'attrs'):
                    raw_link = title_nodes[0].attrs.get('href', 'N/A')
                link = f"https://wuzzuf.net{raw_link}" if raw_link.startswith('/') else raw_link

            company = "N/A"
            company_nodes = job.css('a.css-17s97q8, span.css-17s97q8, div.css-d7j1kk a, a.css-o171kl')
            if company_nodes:
                company = company_nodes[0].text.replace('-', '').strip()
                
            if company == "N/A" or company.lower() == title.lower():
                all_candidates = job.css('a, span')
                for node in all_candidates:
                    node_text = node.text.replace('-', '').strip()
                    if (node_text and node_text.lower() != title.lower() 
                        and node_text.lower() not in ['save', 'apply', 'view details', 'explore']):
                        company = node_text
                        break

            if title and title != "N/A":
                all_jobs.append({"Platform": "Wuzzuf", "Title": title, "Company": company, "Link": link})
    except Exception as e:
        st.warning(f"⚠️ حدث خطأ أثناء سحب بيانات Wuzzuf: {e}")

    # ---------------------------------------------------------
    # 2. LinkedIn
    # ---------------------------------------------------------
    linkedin_url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}&f_TPR=r86400"
    try:
        response_linkedin = StealthyFetcher.fetch(linkedin_url, headless=True, network_idle=True)
        time.sleep(2)
        l_jobs = response_linkedin.css('ul.jobs-search__results-list > li')
        
        for job in l_jobs:
            title_nodes = job.css('.base-search-card__title')
            title = title_nodes[0].text.strip() if title_nodes else "N/A"
            
            link_nodes = job.css('a.base-card__full-link') or job.css('.base-search-card__title a') or job.css('a')
            link = "N/A"
            if link_nodes:
                raw_link = "N/A"
                if hasattr(link_nodes[0], 'attrib'):
                    raw_link = link_nodes[0].attrib.get('href', 'N/A')
                elif hasattr(link_nodes[0], 'attrs'):
                    raw_link = link_nodes[0].attrs.get('href', 'N/A')
                link = raw_link.split('?')[0] if raw_link != "N/A" else "N/A"
            
            company_nodes = job.css('.base-search-card__subtitle a') or job.css('.base-search-card__subtitle')
            company = company_nodes[0].text.strip() if company_nodes else "N/A"
            
            title = re.sub(r'\s+', ' ', title)
            company = re.sub(r'\s+', ' ', company)
            
            if title and title != "N/A" and title != "":
                all_jobs.append({"Platform": "LinkedIn", "Title": title, "Company": company, "Link": link})
    except Exception as e:
        st.warning(f"⚠️ حدث خطأ أثناء سحب بيانات LinkedIn: {e}")

    return all_jobs

def run_in_thread(keyword, location):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(unified_job_scraper, keyword, location)
        return future.result()

# ==========================================
# إعداد واجهة المستخدم (Streamlit UI Setup)
# ==========================================
st.set_page_config(page_title="Intelligent Job Scraper", page_icon="💼", layout="wide")

st.title("💼 نظام البحث الأوتوماتيكي عن الوظائف (Web Job Scraper)")
st.markdown("يقوم هذا التطبيق بجمع أحدث الوظائف المتاحة خلال 24 ساعة من منصات **Wuzzuf** و **LinkedIn**.")

# تقسيم الشاشة إلى أعمدة (Layout Columns)
col1, col2 = st.columns(2)

with col1:
    user_keyword = st.text_input("الوظيفة المستهدفة (Job Title/Keyword)", value="AI Engineer")
with col2:
    user_location = st.text_input("موقع العمل (Location)", value="Egypt")

if st.button("🚀 ابدأ البحث (Start Scraping)", type="primary"):
    if user_keyword and user_location:
        # Streamlit سيحافظ على مؤشر التحميل طوال فترة عمل الدالة
        with st.spinner(f"جاري سحب البيانات عن {user_keyword} في {user_location}... الرجاء الانتظار"):
            
            # استدعاء دالة البحث مباشرة بدون ThreadPoolExecutor
            results = unified_job_scraper(user_keyword, user_location)
            
            if results:
                st.success(f"✅ تم الانتهاء بنجاح! العثور على {len(results)} وظيفة.")
                df = pd.DataFrame(results)
                st.dataframe(
                    df,
                    column_config={
                        "Link": st.column_config.LinkColumn("رابط التقديم (Apply Link)")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 تحميل البيانات (Download CSV)",
                    data=csv,
                    file_name=f"{user_keyword}_jobs.csv",
                    mime="text/csv",
                )
            else:
                st.info("لم يتم العثور على وظائف مطابقة لمعايير البحث في آخر 24 ساعة.")
    else:
        st.error("يرجى إدخال الوظيفة المستهدفة وموقع العمل قبل البدء.")