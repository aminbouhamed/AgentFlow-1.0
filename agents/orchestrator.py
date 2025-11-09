from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import BaseMessage
import operator

# Import all agents
from agents.classifier import classify_email, EmailClassification
from agents.researcher import research_company, CompanyResearch
from agents.rag_agent import RAGAgent, RAGResults
from agents.writer import WriterAgent, EmailResponse
from agents.quality_checker import QualityCheckerAgent, QualityCheck
from agents.decision_agent import DecisionAgent, Decision

class AgentState(TypedDict):
    """
    State that gets passed between agents
    
    This is the "memory" of the workflow
    """
    # Input
    original_email: str
    
    # Agent outputs
    classification: EmailClassification | None
    research: CompanyResearch | None
    rag_results: RAGResults | None
    response: EmailResponse | None
    quality_check: QualityCheck | None
    decision: Decision | None
    
    # Metadata
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_step: str
    error: str | None

class AgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph
    """
    
    def __init__(self):
        # Initialize agents
        self.rag_agent = RAGAgent()
        self.writer_agent = WriterAgent()
        self.quality_checker = QualityCheckerAgent()
        self.decision_agent = DecisionAgent()
        
        # workflow graph
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
    
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes 
        workflow.add_node("classify", self.classify_node)
        workflow.add_node("research", self.research_node)
        workflow.add_node("rag", self.rag_node)
        workflow.add_node("write", self.write_node)
        workflow.add_node("quality_check", self.quality_check_node)
        workflow.add_node("decide", self.decide_node)
        
        # Define edges 
        workflow.set_entry_point("classify")
        
        # the flow
        workflow.add_edge("classify", "research")
        workflow.add_edge("research", "rag")
        workflow.add_edge("rag", "write")
        workflow.add_edge("write", "quality_check")
        workflow.add_edge("quality_check", "decide")
        workflow.add_edge("decide", END)
        
        return workflow
    
    
    # Node functions 
    
    def classify_node(self, state: AgentState) -> AgentState:
        """Classifier agent node"""
        print("\n" + "="*80,flush=True)
        print("1️⃣ CLASSIFIER AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            classification = classify_email(state["original_email"])
            state["classification"] = classification
            state["current_step"] = "classify"
            
            print(f"✅ Classification complete",flush=True)
            print(f"   Intent: {classification.intent}",flush=True)
            print(f"   Company: {classification.company_name}",flush=True)
            
        except Exception as e:
            state["error"] = f"Classifier error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def research_node(self, state: AgentState) -> AgentState:
        """Researcher agent node"""
        print("\n" + "="*80,flush=True)
        print("2️⃣ RESEARCHER AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            classification = state["classification"]
            research = research_company(
                company_name=classification.company_name,
                requirements=classification.key_requirements
            )
            state["research"] = research
            state["current_step"] = "research"
            
            print(f"✅ Research complete",flush=True)
            print(f"   Industry: {research.industry}",flush=True)
            
        except Exception as e:
            state["error"] = f"Research error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def rag_node(self, state: AgentState) -> AgentState:
        """RAG agent node"""
        print("\n" + "="*80,flush=True)
        print("3️⃣ RAG AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            classification = state["classification"]
            research = state["research"]
            
            rag_results = self.rag_agent.retrieve(
                query=" ".join(classification.key_requirements),
                industry=research.industry,
                requirements=classification.key_requirements,
                limit=2
            )
            state["rag_results"] = rag_results
            state["current_step"] = "rag"
            
            print(f"✅ RAG retrieval complete",flush=True)
            print(f"   Documents: {len(rag_results.documents)}",flush=True)
            for i, doc in enumerate(rag_results.documents, 1):
                print(f"{i}. {doc.title}",flush=True)
                print(f"   Score: {doc.relevance_score:.3f}",flush=True)
                print(f"   Category: {doc.category}",flush=True)
                print(f"   Why relevant: {doc.why_relevant}",flush=True)
                print(f"   Snippet: {doc.content[:150]}...",flush=True)
                print()

        except Exception as e:
            state["error"] = f"RAG error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def write_node(self, state: AgentState) -> AgentState:
        """Writer agent node"""
        print("\n" + "="*80,flush=True)
        print("4️⃣ WRITER AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            response = self.writer_agent.write_response(
                classification=state["classification"],
                research=state["research"],
                rag_results=state["rag_results"],
                original_email=state["original_email"]
            )
            state["response"] = response
            state["current_step"] = "write"
            
            print(f"✅ Response written",flush=True)
            print(f"   Length: {len(response.full_email.split())} words",flush=True)
            
        except Exception as e:
            state["error"] = f"Writer error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def quality_check_node(self, state: AgentState) -> AgentState:
        """Quality checker agent node"""
        print("\n" + "="*80,flush=True)
        print("5️⃣ QUALITY CHECKER AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            quality_check = self.quality_checker.check_quality(
                response=state["response"],
                classification=state["classification"],
                original_email=state["original_email"]
            )
            state["quality_check"] = quality_check
            state["current_step"] = "quality_check"
            
            print(f"✅ Quality check complete",flush=True)
            print(f"   Approved: {quality_check.approved}",flush=True)
            print(f"   Confidence: {quality_check.confidence:.2f}",flush=True)
            
        except Exception as e:
            state["error"] = f"Quality check error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def decide_node(self, state: AgentState) -> AgentState:
        """Decision agent node"""
        print("\n" + "="*80,flush=True)
        print("6️⃣ DECISION AGENT",flush=True)
        print("="*80,flush=True)
        
        try:
            decision = self.decision_agent.make_decision(
                quality_check=state["quality_check"],
                classification=state["classification"]
            )
            state["decision"] = decision
            state["current_step"] = "decide"
            
            print(f"✅ Decision made",flush=True)
            print(f"   Action: {decision.action}",flush=True)
            
        except Exception as e:
            state["error"] = f"Decision error: {str(e)}"
            print(f"❌ Error: {e}",flush=True)
        
        return state
    
    def process_email(self, email_text: str) -> AgentState:
        """
        Process an email through the complete agent workflow
        
        Args:
            email_text: Raw email content
            
        Returns:
            Final state with all agent outputs
        """
        print("\n" + "-"*40,flush=True)
        print("STARTING MULTI-AGENT WORKFLOW",flush=True)
        print("-"*40,flush=True)
        
        
        initial_state = AgentState(
            original_email=email_text,
            classification=None,
            research=None,
            rag_results=None,
            response=None,
            quality_check=None,
            decision=None,
            messages=[],
            current_step="start",
            error=None
        )
        
        # Running workflow
        final_state = self.app.invoke(initial_state)
        #Log metrics
        from monitoring.metrics import MetricsCollector
        collector = MetricsCollector()
        collector.log_request(final_state)    
        
        print("\n" + "#"*40,flush=True)
        print("WORKFLOW COMPLETE",flush=True)
        print("#"*40,flush=True)
        
        return final_state

# Test function
if __name__ == "__main__":
    import json
    
    print("="*80)
    print(" Testing LangGraph Orchestrator")
    print("="*80)
    
    # Load test email
    with open('data/sample_emails.json', 'r') as f:
        emails = json.load(f)
    
    #test_email = emails[0]
    #full_text = f"{test_email['subject']}\n\n{test_email['body']}"
    full_text = """Subject: Urgent: API Integration Issues

Hi,

We've been using your AI API for the past 3 weeks but suddenly started getting 429 errors this morning. Our production system is affected and we need immediate assistance.

Error message: "Rate limit exceeded - Quota: 1000 requests/hour"

We're on the Enterprise plan which should have unlimited requests. Please escalate this ASAP.

Thanks,
Sarah Chen
DevOps Lead
DataFlow Solutions
sarah@dataflow.io"""
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Process email
    result = orchestrator.process_email(full_text)
    
    #results
    print("\n" + "="*80)
    print(" FINAL RESULTS")
    print("="*80)
    
    if result["error"]:
        print(f"\n❌ Error occurred: {result['error']}")
    else:
        print(f"\n✅ Workflow completed successfully")
        print(f"   Final step: {result['current_step']}")
        print(f"\n Decision: {result['decision'].action.upper()}")
        print(f"   Priority: {result['decision'].priority}")
        print(f"   Reasoning: {result['decision'].reasoning[:150]}...")
        
        print(f"\n Generated Response:")
        print(f"   Subject: {result['response'].subject}")
        print(f"   Word count: {len(result['response'].full_email.split())}")
        print(f"   Tone: {result['response'].tone}")
        
        print(f"\n" + "-"*80)
        print(result['response'].full_email)
        print("-"*80)