"""
Analyze LangSmith traces to understand agent performance
"""
import os
from langsmith import Client

def analyze_traces():
    """Analyze recent traces from LangSmith"""
    
    client = Client()
    
    print("="*80)
    print(" LANGSMITH TRACE ANALYSIS")
    print("="*80)
    
    project_name = os.getenv("LANGSMITH_PROJECT", "AgentFlow")
    
    print(f"\nProject: {project_name}")
    print(f"Fetching recent runs...\n")
    
    # Get recent runs
    runs = client.list_runs(
        project_name=project_name,
        limit=20
    )
    
    # Analyze
    total_runs = 0
    successful_runs = 0
    total_tokens = 0
    total_latency = 0
    
    agent_calls = {}
    
    for run in runs:
        total_runs += 1
        
        if run.error is None:
            successful_runs += 1
        
        # Track tokens and latency
        if run.total_tokens:
            total_tokens += run.total_tokens
        
        if run.latency:
            total_latency += run.latency
        
        # Track agent calls
        run_name = run.name
        agent_calls[run_name] = agent_calls.get(run_name, 0) + 1
    
    # Print results
    print(f" Summary:")
    print(f"   Total Runs: {total_runs}")
    print(f"   Successful: {successful_runs} ({successful_runs/total_runs*100:.1f}%)")
    
    if total_runs > 0:
        print(f"\n Performance:")
        print(f"   Total Tokens: {total_tokens:,}")
        print(f"   Avg Tokens/Run: {total_tokens/total_runs:.0f}")
        print(f"   Avg Latency: {total_latency/total_runs:.2f}s")
    
    print(f"\n🤖 Agent Call Distribution:")
    for agent, count in sorted(agent_calls.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {agent}: {count} calls")
    
    print("\n" + "="*80)
    print(f" View details at: https://smith.langchain.com/o/YOUR_ORG/projects/p/{project_name}")
    print("="*80)

if __name__ == "__main__":
    analyze_traces()