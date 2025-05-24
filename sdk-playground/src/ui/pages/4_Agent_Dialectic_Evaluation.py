import streamlit as st
import asyncio
from src.data.dataset_generator import DatasetGenerator
from src.ui.components.main_layout import MainLayout
from src.services.evaluation import EvaluationService

def init_session_state():
    if 'datasets' not in st.session_state:
        generator = DatasetGenerator()
        datasets = generator.generate_multiple_datasets([
            {
                "name": "Health Conscious Professionals",
                "num_conversations": 3,
                "router_intent": "Lower BioAge Score"
            },
            {
                "name": "Fitness Enthusiasts",
                "num_conversations": 3,
                "router_intent": "Query Health Analysis"
            },
            {
                "name": "Wellness Beginners",
                "num_conversations": 3,
                "router_intent": "Research Health"
            }
        ])
        st.session_state.datasets = datasets
        st.session_state.current_dataset_index = 0
        st.session_state.current_conversation_index = 0
        st.session_state.current_router_intent = "Lower BioAge Score"
        st.session_state.historical_evaluation_results = []
        st.session_state.evaluation_results = None
        st.session_state.selected_turn_index = None

def render_dataset_selector():
    st.sidebar.header("Dataset Configuration")
    dataset_names = [dataset.name for dataset in st.session_state.datasets]
    selected_dataset = st.sidebar.selectbox(
        "Select User Cohort",
        dataset_names,
        index=st.session_state.current_dataset_index
    )
    router_intents = ["Lower BioAge Score", "Query Health Analysis", "Research Health", "View Health Data as Visualization"]
    selected_intent = st.sidebar.selectbox(
        "AI Coach Router Intent",
        router_intents,
        index=router_intents.index(st.session_state.current_router_intent)
    )
    new_dataset_index = dataset_names.index(selected_dataset)
    if new_dataset_index != st.session_state.current_dataset_index:
        st.session_state.current_dataset_index = new_dataset_index
        st.session_state.current_conversation_index = 0
    if selected_intent != st.session_state.current_router_intent:
        st.session_state.current_router_intent = selected_intent
        generator = DatasetGenerator()
        current_dataset = st.session_state.datasets[st.session_state.current_dataset_index]
        new_dataset = generator.generate_evaluation_dataset(
            num_conversations=len(current_dataset.test_cases),
            router_intent=selected_intent
        )
        new_dataset.name = current_dataset.name
        st.session_state.datasets[st.session_state.current_dataset_index] = new_dataset
        st.session_state.current_conversation_index = 0

async def main():
    init_session_state()
    evaluator = EvaluationService(use_mock=False)
    layout = MainLayout(evaluation_service=evaluator)
    render_dataset_selector()
    st.title("Agent Evaluation")
    current_dataset = st.session_state.datasets[st.session_state.current_dataset_index]
    current_conversation = current_dataset.test_cases[st.session_state.current_conversation_index]
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header(f"Conversation {st.session_state.current_conversation_index + 1} of {len(current_dataset.test_cases)}")
        st.write(f"Dataset: {current_dataset.name}")
        st.write(f"Router Intent: {st.session_state.current_router_intent}")
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if st.button("← Previous", key="prev") and st.session_state.current_conversation_index > 0:
                st.session_state.current_conversation_index -= 1
                st.rerun()
        with nav_col2:
            if st.button("Next →", key="next") and st.session_state.current_conversation_index < len(current_dataset.test_cases) - 1:
                st.session_state.current_conversation_index += 1
                st.rerun()
        st.subheader("Conversation")
        turns = layout.convert_test_case_to_turns(current_conversation)
        for i, turn in enumerate(turns):
            with st.container():
                from src.ui.components.conversation_turn import render_conversation_turn
                render_conversation_turn(
                    turn=turn,
                    is_selected=(i == st.session_state.get('selected_turn_index')),
                )
                if st.button("Select Turn", key=f"select_turn_{i}"):
                    st.session_state.selected_turn_index = i
                    st.rerun()
    with col2:
        with st.expander("Context", expanded=True):
            context = layout.extract_context_from_test_case(current_conversation)
            st.json(context)
        st.subheader("Evaluation")
        if st.button("Run Evaluation", key="eval", type="primary"):
            with st.spinner("Running evaluation with OpenAI..."):
                try:
                    results = await layout.run_evaluation(current_conversation)
                    if results:
                        historical_result = {
                            "timestamp": __import__('datetime').datetime.now().isoformat(),
                            "metrics": results
                        }
                        if 'historical_evaluation_results' not in st.session_state:
                            st.session_state.historical_evaluation_results = []
                        st.session_state.historical_evaluation_results.append(historical_result)
                        layout.metrics_display.render(results)
                        st.info(f"Evaluation cost: ${evaluator.evaluation_cost:.4f}")
                    else:
                        st.error("Evaluation failed to return results")
                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 