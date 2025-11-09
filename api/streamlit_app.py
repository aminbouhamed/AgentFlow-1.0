import streamlit as st
import requests
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AgentFlow - AI Email Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AgentFlow - AI Email Assistant")


with st.sidebar:
    st.header("⚙️ Navigation")
    page = st.radio(
        "Select Page:",
        ["📧 Process Email", "📜 History", "📊 Statistics"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.markdown(f"[API Docs]({API_URL}/docs)")
    st.markdown(f"[Health Check]({API_URL}/health)")

# PAGE 1: 
if page == "📧 Process Email":
    st.header("📧 Email Input")
    
    # Priority selector
    priority = st.selectbox(
        "Priority Level",
        ["low", "normal", "high", "urgent"],
        index=1
    )
    
    
    sample_email = """Subject: AI Implementation Inquiry

Hello,

We are a manufacturing company based in Munich, Germany. We're interested in implementing AI solutions for quality control in our production line.

Could you provide information about:
1. Your AI capabilities for defect detection
2. Integration with existing systems
3. Pricing and timeline

Best regards,
Anna Weber
Quality Manager
AutoParts GmbH"""
    
    email_text = st.text_area(
        "Paste your email here:",
        value=sample_email,
        height=300,
        help="Enter the complete email content including subject and body"
    )
    
  
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        process_button = st.button("🚀 Process Email", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
        if clear_button:
            st.rerun()
    
  
    if process_button:
        if not email_text.strip():
            st.error("❌ Please enter an email to process")
        else:
            with st.spinner("🤖 AI Agents working... (this may take 25-30 seconds)"):
                try:
                    response = requests.post(
                        f"{API_URL}/process",
                        json={
                            "email_text": email_text,
                            "priority": priority
                        },
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        st.success("✅ Email processed successfully!")
                        
                        # Metrics
                        st.header("📊 Processing Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Decision", result['decision'].replace('_', ' ').title())
                        
                        with col2:
                            st.metric("Confidence", f"{result['confidence']*100:.0f}%")
                        
                        with col3:
                            st.metric("Processing Time", f"{result['processing_time']:.1f}s")
                        
                        with col4:
                            quality_status = "✅ Approved" if result['quality_approved'] else "⚠️ Review"
                            st.metric("Quality Check", quality_status)
                        
                        # Response
                        st.header("📧 Generated Response")
                        
                        with st.container():
                            st.subheader(f"Subject: {result['response_subject']}")
                            st.markdown("---")
                            st.text_area(
                                "Response Body:",
                                value=result['response_body'],
                                height=300,
                                disabled=True
                            )
                        
                        # Metadata
                        with st.expander("🔍 Detailed Metadata"):
                            st.json(result['metadata'])
                        
                  
                        st.download_button(
                            label="📋 Download Response",
                            data=result['response_body'],
                            file_name=f"response_{result['request_id']}.txt",
                            mime="text/plain"
                        )
                        
                        st.info("💾 This result has been saved to history")
                    
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.json(response.json())
                
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timeout. Please try again.")
                
                except requests.exceptions.ConnectionError:
                    st.error(f"❌ Cannot connect to API at {API_URL}")
                
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

# PAGE 2:
elif page == "📜 History":
    st.header("📜 Processing History")
    
   
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
            if st.session_state.get('confirm_clear'):
                try:
                    response = requests.delete(f"{API_URL}/history")
                    if response.status_code == 200:
                        st.success("✅ History cleared!")
                        st.session_state['confirm_clear'] = False
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.session_state['confirm_clear'] = True
                st.warning("⚠️ Click again to confirm clearing all history")
    
    
    try:
        response = requests.get(f"{API_URL}/history?limit=50")
        
        if response.status_code == 200:
            history = response.json()
            
            if not history:
                st.info("📭 No history yet. Process some emails to see them here!")
            else:
                st.success(f"📊 Found {len(history)} processed emails")
                
                # Display each entry
                for i, entry in enumerate(history):
                    with st.expander(
                        f"🔹 {entry['decision'].replace('_', ' ').title()} - "
                        f"{entry['created_at'][:19]} - "
                        f"Confidence: {entry['confidence']*100:.0f}%"
                    ):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**Request ID:** `{entry['request_id']}`")
                            st.markdown(f"**Decision:** {entry['decision']}")
                            st.markdown(f"**Confidence:** {entry['confidence']*100:.1f}%")
                            st.markdown(f"**Processing Time:** {entry['processing_time']:.2f}s")
                            st.markdown(f"**Quality Approved:** {'✅ Yes' if entry['quality_approved'] else '⚠️ No'}")
                        
                        with col2:
                            # Delete button
                            if st.button(f"🗑️ Delete", key=f"delete_{entry['request_id']}"):
                                try:
                                    del_response = requests.delete(f"{API_URL}/history/{entry['request_id']}")
                                    if del_response.status_code == 200:
                                        st.success("Deleted!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        # 
                        st.markdown("**📧 Original Email:**")
                        st.text_area(
                            "Email",
                            value=entry['email_text'][:500] + "..." if len(entry['email_text']) > 500 else entry['email_text'],
                            height=100,
                            disabled=True,
                            key=f"email_{i}",
                            label_visibility="collapsed"
                        )
                        
                       
                        st.markdown("**✉️ Generated Response:**")
                        st.markdown(f"**Subject:** {entry['response_subject']}")
                        st.text_area(
                            "Response",
                            value=entry['response_body'],
                            height=150,
                            disabled=True,
                            key=f"response_{i}",
                            label_visibility="collapsed"
                        )
                        
                        # Metadata
                        with st.expander("🔍 Metadata"):
                            st.json(entry['metadata'])
        else:
            st.error(f"❌ Failed to fetch history: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to API at {API_URL}")
    except Exception as e:
        st.error(f"❌ Error fetching history: {str(e)}")

# PAGE 3: Statistics
elif page == "📊 Statistics":
    st.header("📊 Processing Statistics")
    
    # Refresh button
    if st.button("🔄 Refresh Statistics"):
        st.rerun()
    
    try:
        response = requests.get(f"{API_URL}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Processed",
                    stats['total_processed'],
                    help="Total number of emails processed"
                )
            
            with col2:
                st.metric(
                    "Avg Confidence",
                    f"{stats['avg_confidence']*100:.1f}%",
                    help="Average confidence score"
                )
            
            with col3:
                st.metric(
                    "Avg Processing Time",
                    f"{stats['avg_processing_time']:.1f}s",
                    help="Average time to process an email"
                )
            
            with col4:
                st.metric(
                    "Quality Approval Rate",
                    f"{stats['quality_approval_rate']:.1f}%",
                    help="Percentage of responses that passed quality check"
                )
            
            
            st.info("📈 More detailed charts coming soon!")
        else:
            st.error(f"❌ Failed to fetch statistics: {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error fetching statistics: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Built with LangGraph, AWS Bedrock (Claude 3.5), Qdrant & FastAPI</p>
</div>
""", unsafe_allow_html=True)