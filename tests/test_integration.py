import pytest
import time
from agents.orchestrator import AgentOrchestrator

class TestIntegration:
    """Integration tests for the complete agent system"""
    
    @pytest.fixture(scope="class")
    def orchestrator(self):
        """Create orchestrator instance"""
        return AgentOrchestrator()
    
    def test_manufacturing_inquiry(self, orchestrator):
        """Test manufacturing quality control inquiry"""
        
        email = """Subject: AI Implementation Query

Hello,

We're a mid-sized manufacturing company in Munich looking to implement AI 
for quality control. We produce automotive parts and need to detect defects 
in real-time. What solutions do you offer?

Best regards,
Anna Weber
Quality Manager
AutoParts GmbH"""
        
        start_time = time.time()
        result = orchestrator.process_email(email)
        processing_time = time.time() - start_time
        
        # Assertions
        assert result["error"] is None, f"Error occurred: {result['error']}"
        assert result["classification"] is not None
        assert result["classification"].intent == "sales_inquiry"
        assert "autoparts" in result["classification"].company_name.lower()
        
        assert result["research"] is not None
        assert result["research"].industry in ["automotive", "manufacturing"]
        
        assert result["rag_results"] is not None
        assert len(result["rag_results"].documents) > 0
        
        assert result["response"] is not None
        assert len(result["response"].full_email) > 100
        
        assert result["quality_check"] is not None
        assert result["quality_check"].confidence > 0.5
        
        assert result["decision"] is not None
        assert result["decision"].action in ["auto_send", "human_review", "manual_handle"]
        
        # Performance check
        assert processing_time < 30, f"Processing too slow: {processing_time}s"
        
        print(f"\n✅ Manufacturing inquiry test passed ({processing_time:.2f}s)")
    
    def test_partnership_inquiry(self, orchestrator):
        """Test partnership inquiry"""
        
        email = """Subject: Partnership Opportunity

Hi,

I represent a VC firm interested in AI startups. Would love to discuss 
potential collaboration. Are you open to investment discussions?

Best regards,
Thomas Klein
Partner
VentureCapital AG"""
        
        result = orchestrator.process_email(email)
        
        assert result["error"] is None
        assert result["classification"].intent == "partnership"
        assert result["decision"] is not None
        
        print(f"\n✅ Partnership inquiry test passed")
    
    def test_support_request(self, orchestrator):
        """Test technical support request"""
        
        email = """Subject: Technical Support Needed

Our current AI model is showing degraded performance. Can you help us debug? 
We're seeing accuracy drop from 95% to 78% over the past month.

Best regards,
Sarah Müller
ML Engineer
DataCorp"""
        
        result = orchestrator.process_email(email)
        
        assert result["error"] is None
        assert result["classification"].intent == "support_request"
        assert result["response"] is not None
        
        print(f"\n✅ Support request test passed")
    
    def test_response_quality(self, orchestrator):
        """Test that responses meet quality standards"""
        
        email = """Subject: Request for Proposal

We need an AI assistant for our e-commerce platform. Requirements: 
handle 1000+ daily inquiries, German/English support, integrate with Shopify.

Max Fischer
CTO, ShopOnline.de"""
        
        result = orchestrator.process_email(email)
        
        response = result["response"]
        
        
        assert len(response.full_email.split()) < 500, "Response too long"
        assert len(response.full_email.split()) > 100, "Response too short"
        assert response.subject, "Missing subject"
        assert "shopify" in response.full_email.lower() or "e-commerce" in response.full_email.lower(), \
            "Response doesn't address requirements"
        
        print(f"\n✅ Response quality test passed")
    
    def test_error_handling(self, orchestrator):
        """Test error handling with invalid input"""
        
        
        result = orchestrator.process_email("")
        assert result["error"] is not None or result["classification"] is not None
        
        
        result = orchestrator.process_email("Hi")
        
        assert result is not None
        
        print(f"\n✅ Error handling test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])