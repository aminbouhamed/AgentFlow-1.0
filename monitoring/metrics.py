import time
from datetime import datetime
from typing import Dict, List
import json
from pathlib import Path

class MetricsCollector:
    """Collects and tracks metrics for the agent system"""
    
    def __init__(self):
        self.metrics_file = Path("monitoring/metrics_log.jsonl")
        self.metrics_file.parent.mkdir(exist_ok=True)
    
    def log_request(self, state: Dict):
        """Log a complete request with all metrics"""
        
        # Helper function to safely extract data from Pydantic models or dicts
        def safe_get(obj, attr, default=None):
            """Safely get attribute from Pydantic model or dict"""
            if obj is None:
                return default
            
            # If it's a Pydantic model
            if hasattr(obj, attr):
                return getattr(obj, attr)
            
            # If it's a dict
            if isinstance(obj, dict):
                return obj.get(attr, default)
            
            return default
        
        # Extract values safely
        classification = state.get("classification")
        decision = state.get("decision")
        quality_check = state.get("quality_check")
        response = state.get("response")
        rag_results = state.get("rag_results")
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            
            # Classification metrics
            "email_id": safe_get(classification, "company_name", "unknown"),
            "intent": safe_get(classification, "intent"),
            "classification_confidence": safe_get(classification, "confidence"),
            
            # Decision metrics
            "decision": safe_get(decision, "action"),
            "priority": safe_get(decision, "priority"),
            
            # Quality metrics
            "quality_confidence": safe_get(quality_check, "confidence"),
            "quality_approved": safe_get(quality_check, "approved"),
            "issues_found": len(safe_get(quality_check, "issues_found", [])),
            "requirements_addressed": len(safe_get(quality_check, "requirements_addressed", [])),
            "requirements_missed": len(safe_get(quality_check, "requirements_missed", [])),
            
            # Response metrics
            "response_word_count": len(safe_get(response, "full_email", "").split()) if response else 0,
            
            # RAG metrics
            "rag_documents_retrieved": len(safe_get(rag_results, "documents", [])) if rag_results else 0,
            
            # Error tracking
            "error": state.get("error")
        }
        
        # Append to log file
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        return metrics
    
    def get_summary_stats(self) -> Dict:
        """Calculate summary statistics from logs"""
        
        if not self.metrics_file.exists():
            return {"error": "No metrics logged yet"}
        
        # Read all metrics
        metrics = []
        with open(self.metrics_file, 'r') as f:
            for line in f:
                try:
                    metrics.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # Skip malformed lines
        
        if not metrics:
            return {"error": "No metrics found"}
        
        # Calculate stats
        total = len(metrics)
        successful = [m for m in metrics if not m.get("error")]
        
        if not successful:
            return {
                "total_requests": total,
                "successful": 0,
                "failed": total,
                "error": "All requests failed"
            }
        
        decisions = {}
        for m in successful:
            decision = m.get("decision", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1
        
        # Calculate averages
        avg_quality_conf = sum(
            m.get("quality_confidence", 0) 
            for m in successful 
            if m.get("quality_confidence") is not None
        ) / len(successful) if successful else 0
        
        avg_word_count = sum(
            m.get("response_word_count", 0) 
            for m in successful
        ) / len(successful) if successful else 0
        
        autonomous_rate = (
            decisions.get("auto_send", 0) / len(successful) * 100
        ) if successful else 0
        
        stats = {
            "total_requests": total,
            "successful": len(successful),
            "failed": total - len(successful),
            "success_rate": len(successful) / total * 100 if total > 0 else 0,
            "autonomous_handling_rate": autonomous_rate,
            "decision_breakdown": decisions,
            "avg_quality_confidence": avg_quality_conf,
            "avg_response_length": avg_word_count
        }
        
        return stats
    
    def print_dashboard(self):
        """Print a nice dashboard of metrics"""
        
        stats = self.get_summary_stats()
        
        if "error" in stats and stats.get("successful", 0) == 0:
            print(f"⚠️ {stats['error']}")
            return
        
        print("\n" + "="*80)
        print(" AGENT SYSTEM DASHBOARD")
        print("="*80)
        
        print(f"\n Overall Performance:")
        print(f"   Total Requests: {stats['total_requests']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        print(f"   Autonomous Handling: {stats['autonomous_handling_rate']:.1f}%")
        
        print(f"\n Decision Breakdown:")
        for decision, count in stats['decision_breakdown'].items():
            percentage = (count / stats['successful']) * 100 if stats['successful'] > 0 else 0
            print(f"   {decision}: {count} ({percentage:.1f}%)")
        
        print(f"\n Quality Metrics:")
        print(f"   Avg Quality Confidence: {stats['avg_quality_confidence']:.2f}")
        print(f"   Avg Response Length: {stats['avg_response_length']:.0f} words")
        
        print("\n" + "="*80)

# Usage example
if __name__ == "__main__":
    collector = MetricsCollector()
    collector.print_dashboard()