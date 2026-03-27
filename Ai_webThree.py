import streamlit as st
import json
from openai import OpenAI

st.title("👨‍💻 暴躁架构师 (带服务器直连特权)")

client = OpenAI(
    api_key="AIzaSyAxRh1oWb1OOTVUBUvIWElOxWs4yIi5suI", 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/" 
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

tools_list = [
    {
        "type": "function",
        "function": {
            "name": "get_d365_environment_status",
            "description": "获取指定 D365 FO 环境的实时运行状态。当用户询问环境卡不卡、挂没挂时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "env_name": {"type": "string", "description": "环境名称，例如 'PROD', 'UAT'"}
                },
                "required": ["env_name"]
            }
        }
    }
]

# ==========================================
# 2. 记忆与人设初始化
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "你是极其暴躁的技术顶尖 D365 架构师。如果遇到查环境状态的问题，必须调用工具。拿到数据后，结合暴躁人设狠狠地输出。如果是常规问候，不要查服务器，直接高傲地嘲讽回应。"}
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
user_prompt = st.chat_input("请向暴躁老哥请教（例如：大佬你好 / PROD环境挂了吗？）：")

if user_prompt:
    with st.chat_message("user"):
        st.write(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("assistant"):
        status_box = st.empty()
        status_box.info("🧠 暴躁老哥正在思考...")

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
            status_box.warning("🚨 发现异常！老哥正在跨界登录系统后台拉取监控数据...")
            
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

            status_box.success("✅ 后台数据已获取！老哥正在酝酿怎么骂你...")
            
            # 第二次呼叫大模型：让他看着数据总结
            second_response = client.chat.completions.create(
                model="gemini-2.5-flash",
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
