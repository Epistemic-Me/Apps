import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MetricsDisplay:
    def validate_metric_value(self, value: Union[float, None]) -> Optional[float]:
        """Validate a metric value is within acceptable range"""
        if value is None:
            st.warning("Invalid metric value: None")
            return None
        if not isinstance(value, (int, float)):
            st.warning(f"Invalid metric value type: {type(value)}")
            return None
        if value < 0 or value > 1:
            st.warning(f"Metric value out of range [0,1]: {value}")
            return None
        return float(value)

    def render_radar_chart(self, metrics: dict):
        """Render a radar chart of evaluation metrics"""
        categories = list(metrics.keys())
        values = list(metrics.values())
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Metrics'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=False,
            title="Evaluation Metrics"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_metrics_table(self, metrics: dict):
        """Render a table of evaluation metrics"""
        # Create a DataFrame with proper numeric values
        df = pd.DataFrame({
            'Metric': list(metrics.keys()),
            'Score': list(metrics.values())  # Keep as numbers, don't convert to strings yet
        })
        
        # Display metrics in a table with proper formatting
        st.table(df.style.format({
            'Score': '{:.2f}'  # Format numbers as 2 decimal places
        }))
    
    def render(self, metrics: dict):
        """Main render method for the metrics display"""
        if not metrics:
            st.warning("No metrics available")
            return
            
        # Validate and filter metrics
        valid_metrics = {}
        for k, v in metrics.items():
            validated_value = self.validate_metric_value(v)
            if validated_value is not None:
                valid_metrics[k] = validated_value

        if not valid_metrics:
            st.warning("No valid metrics available")
            return

        # Display radar chart
        self.render_radar_chart(valid_metrics)
        
        # Display metrics table
        st.subheader("Detailed Metrics")
        self.render_metrics_table(valid_metrics)
        
        # Calculate and display summary statistics
        avg_score = sum(valid_metrics.values()) / len(valid_metrics)
        best_metric = max(valid_metrics.items(), key=lambda x: x[1])
        worst_metric = min(valid_metrics.items(), key=lambda x: x[1])
        
        # Display summary metrics in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Score", f"{avg_score:.2f}")
        
        with col2:
            st.metric(
                "Strongest Area",
                best_metric[0],
                f"{best_metric[1]:.2f}"
            )
        
        with col3:
            st.metric(
                "Area for Improvement",
                worst_metric[0],
                f"{worst_metric[1]:.2f}"
            )
            
        # Show trends if historical data is available
        if historical_results := st.session_state.get('historical_evaluation_results'):
            self.render_trends(historical_results)

    def get_metric_description(self, metric: str) -> str:
        """Get description for each metric type"""
        descriptions = {
            "user_identification": "Accuracy in identifying user characteristics and needs",
            "belief_evidencing": "Effectiveness in providing evidence for beliefs",
            "belief_verification": "Accuracy in verifying user's beliefs",
            "ambiguity": "Level of clarity in communication (lower is better)",
            "learning_progress": "Progress in achieving learning objectives",
            "answer_prediction": "Accuracy in predicting user responses",
            "question_clarity": "Clarity of questions asked"
        }
        return descriptions.get(metric.lower(), "No description available")

    def render_trends(self, historical_results: Optional[List[Dict]] = None):
        """Render trend visualization for metrics over time"""
        if not historical_results:
            return

        st.markdown("### Metric Trends")

        # Extract timestamps and metrics
        timestamps = []
        metric_values = {}

        for result in historical_results:
            try:
                timestamp = datetime.fromisoformat(result["timestamp"]).strftime("%Y-%m-%d")
                metrics = result["metrics"]
                
                timestamps.append(timestamp)
                for metric, value in metrics.items():
                    if validated_value := self.validate_metric_value(value):
                        if metric not in metric_values:
                            metric_values[metric] = []
                        metric_values[metric].append(validated_value)
            except (KeyError, ValueError) as e:
                st.warning(f"Invalid historical data format: {e}")
                continue

        if not metric_values:
            st.warning("No valid historical data available")
            return

        # Create trend lines for each metric
        fig = go.Figure()
        for metric, values in metric_values.items():
            if len(values) == len(timestamps):  # Only plot if we have all values
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=values,
                    name=metric.replace("_", " ").title(),
                    mode='lines+markers'
                ))

        fig.update_layout(
            title="Metric Trends Over Time",
            xaxis_title="Date",
            yaxis_title="Score",
            yaxis=dict(range=[0, 1]),
            height=400
        )

        st.plotly_chart(fig, use_container_width=True) 