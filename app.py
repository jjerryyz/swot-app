import streamlit as st
from openai import AzureOpenAI
import config_manager
import json
from datetime import datetime

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

def save_history(scenario, questions, answers, analysis):
    """Save analysis history"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    history_item = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scenario': scenario,
        'questions': questions,
        'answers': answers,
        'analysis': analysis
    }
    
    st.session_state.history.append(history_item)
    
    # Save to file
    with open('swot_history.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=2)

def load_history():
    """Load analysis history"""
    try:
        with open('swot_history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def delete_history_item(index):
    """Delete a history item"""
    st.session_state.history.pop(index)
    with open('swot_history.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=2)

def show_history():
    """Show analysis history in sidebar"""
    with st.sidebar:
        # Add a button to go back to configuration
        if st.button("⚙️ 配置 OpenAI"):
            st.session_state.page = "config"
            st.rerun()

        st.title("历史记录")
        
        # Add new analysis button
        if st.button("➕ 新建分析"):
            # Clear current analysis state
            if 'questions' in st.session_state:
                del st.session_state.questions
            if 'answers' in st.session_state:
                del st.session_state.answers
            if 'scenario' in st.session_state:
                del st.session_state.scenario
            if 'analysis' in st.session_state:
                del st.session_state.analysis
            st.session_state.page = "analysis"
            st.rerun()
        
        if not st.session_state.history:
            st.info("暂无历史记录")
            return
        
        # Show history items
        for idx, item in enumerate(reversed(st.session_state.history)):
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"{item['timestamp']} - {item['scenario'][:30]}...",
                    key=f"history_{idx}",
                    use_container_width=True
                ):
                    # Load the history item
                    st.session_state.scenario = item['scenario']
                    st.session_state.questions = item['questions']
                    st.session_state.answers = item['answers']
                    st.session_state.analysis = item['analysis']
                    st.session_state.page = "analysis"
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"delete_{idx}"):
                    delete_history_item(len(st.session_state.history) - 1 - idx)
                    st.rerun()

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
        st.session_state.openai_config['deployment_name'] = st.text_input(
            "部署名称",
            value=st.session_state.openai_config['deployment_name']
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

def check_answers_complete():
    """Check if all answers are filled"""
    if 'answers' not in st.session_state:
        return False
    
    for category in ['优势', '劣势', '机会', '威胁']:
        for answer in st.session_state.answers[category]:
            if not answer.strip():
                return False
    return True

def show_analysis_page():
    """Show the SWOT analysis page"""
    st.title("SWOT 分析助手")
    
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
    scenario = st.text_area("请输入您的场景：", height=100)
    
    # Add scenario confirmation button
    if scenario and 'questions' not in st.session_state:
        if st.button("确认场景并生成问题"):
            with st.spinner("正在生成问题..."):
                questions_text = get_swot_questions(scenario)
                st.session_state.questions = parse_swot_questions(questions_text)
                st.session_state.answers = {
                    '优势': [''] * len(st.session_state.questions['优势']),
                    '劣势': [''] * len(st.session_state.questions['劣势']),
                    '机会': [''] * len(st.session_state.questions['机会']),
                    '威胁': [''] * len(st.session_state.questions['威胁'])
                }
                st.session_state.scenario = scenario
                st.rerun()
    
    # Display questions and collect answers if they exist
    if 'questions' in st.session_state:
        st.info(f"当前分析场景：{st.session_state.scenario}")
        
        # Create two columns for questions and analysis
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("SWOT 分析问题")
            # Create a container for questions with scrolling
            questions_container = st.container()
            with questions_container:
                # Add custom CSS for scrolling
                st.markdown("""
                    <style>
                    .questions-container {
                        max-height: 600px;
                        overflow-y: auto;
                        padding-right: 10px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # Wrap questions in a div with custom class
                st.markdown('<div class="questions-container">', unsafe_allow_html=True)
                for category in ['优势', '劣势', '机会', '威胁']:
                    st.markdown(f"### {category}")
                    for i, question in enumerate(st.session_state.questions[category]):
                        st.session_state.answers[category][i] = st.text_area(
                            f"{category} {i+1}: {question}",
                            value=st.session_state.answers[category][i],
                            key=f"{category}_{i}",
                            height=100
                        )
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.subheader("分析结果")
            # Create a container for analysis with scrolling
            analysis_container = st.container()
            with analysis_container:
                # Add custom CSS for scrolling
                st.markdown("""
                    <style>
                    .analysis-container {
                        max-height: 600px;
                        overflow-y: auto;
                        padding-right: 10px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                if 'analysis' in st.session_state:
                    # Add copy button
                    if st.button("📋 复制分析结果", key="copy_analysis"):
                        st.write(f'<script>navigator.clipboard.writeText(`{st.session_state.analysis}`)</script>', unsafe_allow_html=True)
                        st.success("已复制到剪贴板！")
                    
                    # Wrap analysis in a div with custom class
                    st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
                    st.write(st.session_state.analysis)
                    st.markdown('</div>', unsafe_allow_html=True)
        
        # Check if all answers are filled before enabling the analyze button
        if check_answers_complete():
            if st.button("分析"):
                # Format answers for analysis
                formatted_answers = ""
                for category in ['优势', '劣势', '机会', '威胁']:
                    formatted_answers += f"\n{category}：\n"
                    for i, answer in enumerate(st.session_state.answers[category]):
                        formatted_answers += f"{i+1}. {answer}\n"
                
                with st.spinner("正在分析..."):
                    analysis = analyze_swot_answers(st.session_state.scenario, formatted_answers)
                    st.session_state.analysis = analysis
                    
                    # Save to history
                    save_history(
                        st.session_state.scenario,
                        st.session_state.questions,
                        st.session_state.answers,
                        analysis
                    )
                    st.rerun()
        else:
            st.warning("请填写所有问题的答案后再进行分析。")

def main():
    # Initialize page state if not exists
    if 'page' not in st.session_state:
        st.session_state.page = "analysis"
    
    # Initialize configuration if not exists
    if 'openai_config' not in st.session_state:
        st.session_state.openai_config = config_manager.load_config()
    
    # Initialize history if not exists
    if 'history' not in st.session_state:
        st.session_state.history = load_history()
    
    # Show history in sidebar
    show_history()
    
    # Show appropriate page based on state
    if st.session_state.page == "config":
        show_config_page()
    else:
        show_analysis_page()

if __name__ == "__main__":
    main() 