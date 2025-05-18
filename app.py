import streamlit as st
from openai import AzureOpenAI
import config_manager


st.set_page_config(layout="wide")

def init_openai_client():
    """Initialize Azure OpenAI client with user configuration"""
    return AzureOpenAI(
        api_key=st.session_state.openai_config['api_key'],
        api_version=st.session_state.openai_config['api_version'],
        azure_endpoint=st.session_state.openai_config['endpoint']
    )

def get_swot_questions(scenario):
    """Generate SWOT questions based on the scenario"""
    client = init_openai_client()
    prompt = f"""基于以下场景，为每个 SWOT 类别（优势、劣势、机会、威胁）生成 2-3 个具体问题：

场景：{scenario}

请按照以下格式输出：
优势：
1. [问题]
2. [问题]

劣势：
1. [问题]
2. [问题]

机会：
1. [问题]
2. [问题]

威胁：
1. [问题]
2. [问题]"""

    response = client.chat.completions.create(
        model=st.session_state.openai_config['deployment_name'],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content

def analyze_swot_answers(scenario, answers):
    """Analyze the SWOT answers and provide insights"""
    client = init_openai_client()
    prompt = f"""基于以下场景和 SWOT 分析答案，提供全面的分析和建议：

场景：{scenario}

SWOT 分析答案：
{answers}

请提供：
1. 关键发现总结
2. 主要优势及如何利用
3. 关键劣势及如何改进
4. 重要机会及如何把握
5. 主要威胁及如何应对
6. 整体建议和下一步行动方案"""

    response = client.chat.completions.create(
        model=st.session_state.openai_config['deployment_name'],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content

def parse_swot_questions(questions_text):
    """Parse the SWOT questions into a structured format"""
    questions = {
        '优势': [],
        '劣势': [],
        '机会': [],
        '威胁': []
    }
    
    current_category = None
    for line in questions_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line in ['优势：', '劣势：', '机会：', '威胁：']:
            current_category = line[:-1]
        elif current_category and line[0].isdigit():
            questions[current_category].append(line[3:])
            
    return questions

def show_config_page():
    """Show the configuration page"""
    st.title("Azure OpenAI 配置")
    
    # Initialize configuration if not exists
    if 'openai_config' not in st.session_state:
        st.session_state.openai_config = config_manager.load_config()
    
    # Configuration form
    with st.form("openai_config_form"):
        st.session_state.openai_config['api_key'] = st.text_input(
            "Azure OpenAI API 密钥",
            value=st.session_state.openai_config['api_key'],
            type="password"
        )
        st.session_state.openai_config['endpoint'] = st.text_input(
            "Azure OpenAI 终端点",
            value=st.session_state.openai_config['endpoint']
        )
        st.session_state.openai_config['deployment_name'] = st.selectbox(
            "部署名称",
            ("gpt-4o-mini","gpt-4o", "gpt-35-turbo")
        )
        st.session_state.openai_config['api_version'] = st.text_input(
            "API 版本",
            value=st.session_state.openai_config['api_version']
        )
        
        submitted = st.form_submit_button("保存配置")
        if submitted:
            # Save configuration to file
            config_manager.save_config(st.session_state.openai_config)
            st.success("配置保存成功！")
            st.session_state.page = "analysis"
            st.rerun()

def show_question_section(category):
    st.markdown(f"### {category}")
    for i, question in enumerate(st.session_state.questions[category]):
        st.session_state.answers[category][i] = st.text_area(
            f"{category} {i+1}: {question}",
            value=st.session_state.answers[category][i],
            key=f"{category}_{i}"
        )

@st.fragment()
def show_questions():
    with st.container(height=800):
        # Display questions and collect answers
        st.subheader("SWOT 分析问题")
        
        tab1, tab2, tab3, tab4 = st.tabs(["优势", "劣势", "机会", "威胁"])
        with tab1:
            show_question_section("优势")
        with tab2:
            show_question_section("劣势")
        with tab3:
            show_question_section("机会")
        with tab4:
            show_question_section("威胁")

@st.fragment()
def show_result():
    with st.container(height=800):
        if st.button("分析"):
            # Format answers for analysis
            formatted_answers = ""
            for category in ['优势', '劣势', '机会', '威胁']:
                formatted_answers += f"\n{category}：\n"
                for i, answer in enumerate(st.session_state.answers[category]):
                    formatted_answers += f"{i+1}. {answer}\n"
            
            with st.spinner("正在分析..."):
                analysis = analyze_swot_answers(st.session_state.scenario, formatted_answers)
                st.subheader("分析结果")
                st.write(analysis)

def show_analysis_page():
    """Show the SWOT analysis page"""
    st.title("SWOT 分析助手")
    
    # Add a button to go back to configuration
    if st.button("⚙️ 配置 OpenAI"):
        st.session_state.page = "config"
        st.rerun()
    
    # Check if OpenAI is configured
    if not all([st.session_state.openai_config['api_key'], 
                st.session_state.openai_config['endpoint'],
                st.session_state.openai_config['deployment_name']]):
        st.warning("请先配置 Azure OpenAI 设置。")
        if st.button("前往配置"):
            st.session_state.page = "config"
            st.rerun()
        return

    st.write("请输入您的场景，我们将帮助您进行 SWOT 分析。")

    # Input scenario
    st.session_state.scenario = st.text_area("请输入您的场景：", height=100)

    
    if not st.session_state.scenario:
        return
    if not st.button("生成问题"):
        return
    if 'questions' not in st.session_state:
        questions_text = get_swot_questions(st.session_state.scenario)
        st.session_state.questions = parse_swot_questions(questions_text)
        st.session_state.answers = {
            '优势': [''] * len(st.session_state.questions['优势']),
            '劣势': [''] * len(st.session_state.questions['劣势']),
            '机会': [''] * len(st.session_state.questions['机会']),
            '威胁': [''] * len(st.session_state.questions['威胁'])
        }
    col1, col2 = st.columns(2)
    
    with col1:
        show_questions()
        
    with col2:
        show_result()

def main():
    # Initialize page state if not exists
    if 'page' not in st.session_state:
        st.session_state.page = "config"
    
    # Initialize configuration if not exists
    if 'openai_config' not in st.session_state:
        st.session_state.openai_config = config_manager.load_config()
    
    # Show appropriate page based on state
    if st.session_state.page == "config":
        show_config_page()
    else:
        show_analysis_page()

if __name__ == "__main__":
    main() 