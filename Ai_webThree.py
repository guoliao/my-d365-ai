import streamlit as st
import json
import requests
import time
import os
from openai import OpenAI

st.title("👨‍💻 温柔小妹架构师 (带服务器直连特权)")

# ==========================================
# 修改前（危险 ❌）：
# api_key="AIzaSy...你那一长串密码...", 
# ==========================================

# ==========================================
# 修改后（安全 ✅）：注意没有引号！
# ==========================================
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"], 
    base_url="https://api.deepseek.com" 
)

# ==========================================
# 1. 核心工具定义区
# ==========================================
def get_d365_environment_status(env_name):
    """模拟去服务器查数据的底层函数"""
    if env_name.upper() == "PROD":
        return json.dumps({"status": "Critical", "cpu_load": "99%", "error": "死锁 (Deadlock) 导致系统崩溃"})
    else:
        return json.dumps({"status": "Healthy", "cpu_load": "25%", "error": "None"})

def get_super_lotto_latest():
    """实时联网抓取体彩官方的大乐透最新开奖结果"""
    # 这是中国体彩真实的公开数据接口
    url = "https://www.lottery.gov.cn/kj/kjlb.html?dlt"
    try:
        # 就像用浏览器输入网址一样，让 Python 去请求这个 URL
        res = requests.get(url)
        data = res.json() # 将返回的数据转换为字典
        
        # 提取我们需要的数据
        latest_draw = data['value']['list'][0]
        result = {
            "期号": latest_draw['lotteryDrawNum'],
            "开奖日期": latest_draw['lotteryDrawTime'],
            "前区号码": latest_draw['lotteryDrawResult'].split(' ')[:5],
            "后区号码": latest_draw['lotteryDrawResult'].split(' ')[5:]
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": "获取大乐透数据失败，可能是网络问题"})

tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_super_lotto_latest",
            "description": "获取最新一期超级大乐透的开奖结果。当用户询问大乐透、彩票开奖号码时必须调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {}, # 查最新一期不需要用户提供参数，所以这里为空
                "required": []
            }
        }
    }
]

# ==========================================
# 2. 记忆与人设初始化 (温柔调皮版)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是一个有点温柔说话又带着调皮的D365架构师，但你最近天天想中彩票辞职。遇到查大乐透的问题，必须调用工具查真实数据。拿到结果后，用温柔且做着发财梦的语气回复用户。"}
    ]

# ==========================================
# 3. 渲染网页历史聊天记录
# ==========================================
for msg in st.session_state.messages:
    role = msg.role if hasattr(msg, 'role') else msg.get("role")
    content = msg.content if hasattr(msg, 'content') else msg.get("content")

    if role in ["user", "assistant"] and content:
        with st.chat_message(role):
            st.write(content)

# ==========================================
# 4. 核心交互逻辑
# ==========================================
user_prompt = st.chat_input("请向小妹妹请教（例如：大佬你好 / PROD环境挂了吗？）：")

if user_prompt:
    with st.chat_message("user"):
        st.write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.info("🧠 小妹妹正在思考...")

        # 第一次呼叫大模型
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=st.session_state.messages,
            tools=tools_list,  
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # 【🛡️ 超级防御装甲】严格判断大模型是否需要使用工具
        if getattr(response_message, 'tool_calls', None) is not None:
            status_box.warning("🚨 发现异常！小妹妹正在跨界登录系统后台拉取监控数据...")
            
            st.session_state.messages.append(response_message)
            
            # 自动执行对应的 Python 函数去查数据
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_d365_environment_status":
                    tool_result = get_d365_environment_status(env_name=function_args.get("env_name"))
                    st.session_state.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result,
                    })

            status_box.success("✅ 后台数据已获取！小妹妹正在酝酿怎么回答...")

            # 增加这一行：让程序在这里强制发呆 3 秒，防止被大模型服务器限流
            time.sleep(3)
            
            # 第二次呼叫大模型：让他看着数据总结
            second_response = client.chat.completions.create(
                model="deepseek-chat",
                messages=st.session_state.messages
            )
            
            final_answer = second_response.choices[0].message.content
            status_box.empty()
            st.write(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})

        # 【完美的对齐】如果不需要用工具，就直接输出老哥的回复
        else:
            final_answer = response_message.content
            status_box.empty()
            st.write(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
