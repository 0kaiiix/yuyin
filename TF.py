#
import streamlit as st
import ollama
from gtts.lang import tts_langs
from gtts import gTTS
import base64
from tempfile import NamedTemporaryFile
import time
from streamlit_lottie import st_lottie
import requests
import json
#streamlit run TF.py

# 頁面配置和樣式設定
st.set_page_config(
    page_title="AI 語音助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        padding: 10px 24px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition-duration: 0.4s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
    }
    .css-1fkbmr4 {
        font-size: 36px;
        font-weight: bold;
        color: #2e4057;
        margin-bottom: 20px;
    }
    .css-q8sbsg p {
        font-size: 18px;
        line-height: 1.6;
    }
    .user-question {
        background-color: #e8f4fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #4361ee;
        color: #000000;
    }
    .bot-response {
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #3a86ff;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# 加載Lottie動畫
def load_lottieurl(url):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        st.error(f"無法載入動畫: {e}")
        return None

# 預設動畫數據 (簡單的動畫JSON)
default_animation = {
    "v": "5.8.1",
    "fr": 30,
    "ip": 0,
    "op": 60,
    "w": 100,
    "h": 100,
    "nm": "Loading Animation",
    "ddd": 0,
    "assets": [],
    "layers": [{
        "ddd": 0,
        "ind": 1,
        "ty": 4,
        "nm": "Circle",
        "sr": 1,
        "ks": {
            "o": {"a": 0, "k": 100},
            "r": {
                "a": 1,
                "k": [{"t": 0, "s": [0], "e": [360]}, {"t": 60, "s": [360], "e": [720]}]
            },
            "p": {"a": 0, "k": [50, 50, 0]},
            "a": {"a": 0, "k": [0, 0, 0]},
            "s": {"a": 0, "k": [100, 100, 100]}
        },
        "shapes": [{
            "ty": "el",
            "d": 1,
            "s": {"a": 0, "k": [40, 40]},
            "p": {"a": 0, "k": [0, 0]},
            "nm": "Ellipse Path 1",
            "mn": "ADBE Vector Shape - Ellipse"
        }, {
            "ty": "st",
            "c": {"a": 0, "k": [0.2, 0.6, 1, 1]},
            "o": {"a": 0, "k": 100},
            "w": {"a": 0, "k": 8},
            "lc": 2,
            "lj": 1,
            "ml": 4,
            "nm": "Stroke 1",
            "mn": "ADBE Vector Graphic - Stroke"
        }, {
            "ty": "tr",
            "p": {"a": 0, "k": [0, 0]},
            "a": {"a": 0, "k": [0, 0]},
            "s": {"a": 0, "k": [100, 100]},
            "r": {"a": 0, "k": 0},
            "o": {"a": 0, "k": 100},
            "sk": {"a": 0, "k": 0},
            "sa": {"a": 0, "k": 0}
        }]
    }]
}

# 加載動畫 (使用備用選項)
lottie_bot_url = "https://assets6.lottiefiles.com/packages/lf20_QUshUY.json"
lottie_voice_url = "https://assets9.lottiefiles.com/packages/lf20_ystsffqy.json"

lottie_bot = load_lottieurl(lottie_bot_url) or default_animation
lottie_voice = load_lottieurl(lottie_voice_url) or default_animation

# 側邊欄
with st.sidebar:
    st.markdown("### ⚙️ 設定")
    langs = tts_langs().keys()
    lang = st.selectbox("選擇語言", options=langs, index=12)  # en 12
    
    st.markdown("---")
    st.markdown("### 🤖 關於")
    st.markdown("這是一個使用Gemma 3和gTTS的AI對話與語音合成應用")
    
    # 顯示小機器人動畫在側邊欄
    try:
        st_lottie(lottie_bot, height=200, key="sidebar_bot")
    except Exception as e:
        st.image("https://via.placeholder.com/200x200.png?text=AI+Assistant", caption="AI 助手")

# 主畫面
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🤖 AI 語音助手")
    st.markdown("### 與 Gemma 3 模型即時對話，並聆聽 AI 的回應")

# 聊天容器
chat_container = st.container()

# 用戶輸入區
with st.container():
    user_input = st.text_area("✍️ 請輸入您的問題：", "", height=100, 
                               placeholder="在這裡輸入您想問的任何問題...", 
                               help="您可以用任何語言提問，AI將嘗試理解並回應")
    
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        send_button = st.button("🚀 發送問題", use_container_width=True)

# 聊天紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示聊天記錄
with chat_container:
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"<div class='user-question'><strong style='color:#000000;'>您:</strong> <span style='color:#000000;'>{message['content']}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-response'><strong style='color:#000000;'>AI:</strong> <span style='color:#000000;'>{message['content']}</span></div>", unsafe_allow_html=True)

if send_button:
    if user_input:
        # 添加用戶訊息到聊天記錄
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 顯示思考中的動畫
        with st.spinner("AI 正在思考中..."):
            # 顯示思考動畫
            thinking_placeholder = st.empty()
            col1, col2, col3 = thinking_placeholder.columns([1, 2, 1])
            with col2:
                try:
                    st_lottie(lottie_bot, height=150, key="thinking")
                except Exception:
                    st.markdown("⏳ **AI正在處理您的請求...**")
            
            # 發送請求到Gemma模型
            try:
                response = ollama.chat(model='gemma3:1b', messages=[{'role': 'user', 'content': user_input}])
                ai_response = response['message']['content']
            except Exception as e:
                ai_response = f"抱歉，處理您的請求時發生錯誤: {str(e)}"
                st.error(f"錯誤: {str(e)}")
            
            # 添加AI回應到聊天記錄
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            # 清除思考動畫
            thinking_placeholder.empty()
        
        # 更新聊天紀錄顯示
        chat_container.empty()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"<div class='user-question'><strong style='color:#000000;'>您:</strong> <span style='color:#000000;'>{message['content']}</span></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='bot-response'><strong style='color:#000000;'>AI:</strong> <span style='color:#000000;'>{message['content']}</span></div>", unsafe_allow_html=True)
        
        # 語音合成部分
        with st.spinner("正在生成語音..."):
            voice_placeholder = st.empty()
            col1, col2, col3 = voice_placeholder.columns([1, 2, 1])
            with col2:
                try:
                    st_lottie(lottie_voice, height=150, key="voice_generating")
                except Exception:
                    st.markdown("🔊 **正在生成語音...**")
            
            try:
                tts = gTTS(ai_response, lang=lang, slow=False, lang_check=True)
                with NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
                    tts.save(temp.name)
                    with open(temp.name, "rb") as f:
                        data = f.read()
                        b64 = base64.b64encode(data).decode()
                        
                        # 清除語音動畫
                        voice_placeholder.empty()
                        
                        # 顯示語音播放器
                        st.markdown("<h3 style='text-align: center;'>🔊 語音回應</h3>", unsafe_allow_html=True)
                        md = f"""<div style="display: flex; justify-content: center;">
                             <audio controls autoplay="true" style="width: 100%; max-width: 500px;">
                             <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                             您的瀏覽器不支援音訊元素。</audio></div>"""
                        st.markdown(md, unsafe_allow_html=True)
            except Exception as e:
                voice_placeholder.empty()
                st.error(f"無法生成語音: {str(e)}")
    else:
        st.warning("⚠️ 請輸入您的問題！")
