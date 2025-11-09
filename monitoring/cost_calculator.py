"""
Calculate estimated costs for agent operations
"""


PRICING = {
    "claude-3-5-sonnet": {
        "input": 0.003 / 1000,   
        "output": 0.015 / 1000    
    },
    "claude-3-haiku": {
        "input": 0.00025 / 1000,  
        "output": 0.00125 / 1000  
    },
    "titan-embeddings": {
        "input": 0.0001 / 1000,  
        "output": 0
    }
}

# token usage per agent
AGENT_TOKEN_USAGE = {
    "classifier": {
        "model": "claude-3-haiku",
        "input_tokens": 500,
        "output_tokens": 100
    },
    "researcher": {
        "model": "claude-3-5-sonnet",
        "input_tokens": 2000,
        "output_tokens": 500
    },
    "rag": {
        "model": "titan-embeddings",
        "input_tokens": 500,
        "output_tokens": 0
    },
    "writer": {
        "model": "claude-3-5-sonnet",
        "input_tokens": 3000,
        "output_tokens": 800
    },
    "quality_checker": {
        "model": "claude-3-haiku",
        "input_tokens": 1500,
        "output_tokens": 200
    }
}

def calculate_cost_per_request():
    """Calculate cost per email processed"""
    
    total_cost = 0
    
    print("="*80)
    print(" COST BREAKDOWN PER REQUEST")
    print("="*80)
    
    for agent_name, usage in AGENT_TOKEN_USAGE.items():
        model = usage["model"]
        pricing = PRICING[model]
        
        input_cost = usage["input_tokens"] * pricing["input"]
        output_cost = usage["output_tokens"] * pricing["output"]
        agent_cost = input_cost + output_cost
        
        total_cost += agent_cost
        
        print(f"\n{agent_name.upper()} ({model}):")
        print(f"   Input: {usage['input_tokens']:,} tokens × ${pricing['input']*1000:.4f}/1K = ${input_cost:.6f}")
        print(f"   Output: {usage['output_tokens']:,} tokens × ${pricing['output']*1000:.4f}/1K = ${output_cost:.6f}")
        print(f"   Subtotal: ${agent_cost:.6f}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL COST PER REQUEST: ${total_cost:.6f}")
    print(f"{'='*80}")
    
    
    print(f"\n Cost Projections:")
    volumes = [100, 1000, 10000, 100000]
    for volume in volumes:
        cost = total_cost * volume
        print(f"   {volume:,} emails/month: ${cost:.2f}")
    
    print(f"\nCost Optimization Tips:")
    print(f"   1. Cache embeddings for repeated queries (saves ~20%)")
    print(f"   2. Use Haiku for more tasks where possible (5-10x cheaper)")
    print(f"   3. Batch RAG operations (reduces API calls)")
    print(f"   4. Implement prompt compression (reduce input tokens)")
    
    return total_cost

def calculate_cost_with_caching():
    """Calculate cost with caching optimizations"""
    
    base_cost = calculate_cost_per_request()
    
    print(f"\n\n{'='*80}")
    print(" WITH OPTIMIZATIONS (Caching + Batching)")
    print("="*80)
    
    
    cache_hit_rate = 0.30
    token_reduction = 0.20
    
    optimized_cost = base_cost * (1 - token_reduction)
    
    # Calculate savings
    cached_requests = cache_hit_rate
    full_requests = 1 - cache_hit_rate
    
    # Skipping rag in case of cache hit
    rag_cost = (
        AGENT_TOKEN_USAGE["rag"]["input_tokens"] * PRICING["titan-embeddings"]["input"]
    )
    
    avg_cost_with_cache = (
        full_requests * optimized_cost +
        cached_requests * (optimized_cost - rag_cost)
    )
    
    print(f"\nBase cost: ${base_cost:.6f}")
    print(f"With optimizations: ${avg_cost_with_cache:.6f}")
    print(f"Savings: {(1 - avg_cost_with_cache/base_cost)*100:.1f}%")
    
    print(f"\n Optimized Cost Projections:")
    volumes = [100, 1000, 10000, 100000]
    for volume in volumes:
        cost = avg_cost_with_cache * volume
        savings = (base_cost - avg_cost_with_cache) * volume
        print(f"   {volume:,} emails/month: ${cost:.2f} (save ${savings:.2f})")

if __name__ == "__main__":
    calculate_cost_with_caching()