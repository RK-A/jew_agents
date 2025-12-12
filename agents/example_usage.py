"""Example usage of AI agents for jewelry consultation and analysis"""

import asyncio
from config import settings
from llm.factory import create_llm_provider
from rag import create_embedding_provider, QdrantService
from agents import AgentOrchestrator


async def example_consultant_agent():
    """Example: Using ConsultantAgent for customer consultation"""
    
    print("\n" + "="*60)
    print("EXAMPLE 1: Consultant Agent")
    print("="*60)
    
    # Initialize LLM and RAG
    llm_provider = create_llm_provider(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature
    )
    
    embedding_provider = create_embedding_provider(
        model=settings.embedding_model,
        api_key=settings.embedding_api_key
    )
    
    qdrant_service = QdrantService(
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
        embedding_provider=embedding_provider
    )
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        rag_service=qdrant_service
    )
    
    # Example consultation
    user_id = "user_001"
    message = "Я ищу обручальное кольцо для невесты, бюджет до 80 тысяч рублей. Она любит классический стиль."
    
    print(f"\nUser: {message}")
    
    result = await orchestrator.handle_user_consultation(
        user_id=user_id,
        message=message
    )
    
    if result["status"] == "success":
        consultation_result = result["result"]
        print(f"\nAgent Response:\n{consultation_result['response']}")
        print(f"\nRecommendations: {len(consultation_result['recommendations'])} products")
        print(f"Extracted Preferences: {consultation_result['extracted_preferences']}")
    else:
        print(f"Error: {result.get('error')}")


async def example_analysis_agent():
    """Example: Using AnalysisAgent for customer analysis"""
    
    print("\n" + "="*60)
    print("EXAMPLE 2: Customer Analysis Agent")
    print("="*60)
    
    # Initialize LLM
    llm_provider = create_llm_provider(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature
    )
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        rag_service=None
    )
    
    print("\nRunning customer analysis...")
    
    result = await orchestrator.run_customer_analysis()
    
    if result["status"] == "success":
        analysis_result = result["result"]
        print(f"\nAnalysis Status: {analysis_result['status']}")
        
        if analysis_result["status"] == "success":
            print(f"Total Customers Analyzed: {analysis_result['total_customers']}")
            print(f"\nPopular Styles: {analysis_result['patterns'].get('popular_styles', {})}")
            print(f"Popular Materials: {analysis_result['patterns'].get('popular_materials', {})}")
            print(f"Average Budget: {analysis_result['patterns'].get('average_budget', 0)}₽")
            print(f"\nCustomer Segments: {len(analysis_result['customer_segments'])}")
            
            print(f"\n--- Analysis Report Preview ---")
            print(analysis_result['report'][:500] + "...")
        else:
            print(f"No data available: {analysis_result.get('message')}")
    else:
        print(f"Error: {result.get('error')}")


async def example_trend_agent():
    """Example: Using TrendAgent for fashion trend analysis"""
    
    print("\n" + "="*60)
    print("EXAMPLE 3: Trend Analysis Agent")
    print("="*60)
    
    # Initialize LLM
    llm_provider = create_llm_provider(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature
    )
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        rag_service=None
    )
    
    # Sample fashion journal content
    fashion_content = """
    Spring 2024 Jewelry Trends: A Return to Classic Elegance
    
    This season sees a resurgence of classic gold jewelry with modern twists.
    Designers are embracing minimalist aesthetics, featuring delicate chains,
    stackable rings, and geometric pendants. White gold and platinum continue
    to dominate high-end collections, particularly in engagement rings.
    
    Pearls are making a major comeback, no longer confined to traditional
    necklaces but appearing in bold, contemporary designs. Statement earrings
    with diamond accents are the must-have accessory for formal occasions.
    
    The vintage-inspired art deco style is trending, with emerald and sapphire
    gemstones taking center stage. Layered necklaces and chunky bracelets
    offer a bohemian vibe perfect for everyday wear.
    
    Celebrity favorite designers include Cartier, Tiffany & Co., and emerging
    independent jewelers focusing on sustainable luxury pieces.
    """
    
    print(f"\nAnalyzing fashion content ({len(fashion_content)} characters)...")
    
    result = await orchestrator.run_trend_analysis(content=fashion_content)
    
    if result["status"] == "success":
        trend_result = result["result"]
        print(f"\nTrend Analysis Status: {trend_result['status']}")
        
        if trend_result["status"] == "success":
            print(f"\nIdentified Trends:")
            trends = trend_result['identified_trends']
            print(f"  - Trending Styles: {trends.get('trending_styles', [])}")
            print(f"  - Popular Materials: {trends.get('popular_materials', [])}")
            print(f"  - Trending Colors: {trends.get('trending_colors', [])}")
            print(f"  - Mentioned Designers: {trends.get('mentioned_designers', [])}")
            
            print(f"\nEmerging Trends: {trend_result['emerging_trends']}")
            
            print(f"\nRecommendations: {len(trend_result['recommendations'])}")
            for rec in trend_result['recommendations'][:3]:
                print(f"  [{rec['priority']}] {rec['type']}: {rec['action']}")
            
            print(f"\n--- Trend Report Preview ---")
            print(trend_result['report'][:500] + "...")
    else:
        print(f"Error: {result.get('error')}")


async def example_orchestrator_status():
    """Example: Check orchestrator and agent status"""
    
    print("\n" + "="*60)
    print("EXAMPLE 4: Orchestrator Status")
    print("="*60)
    
    # Initialize LLM
    llm_provider = create_llm_provider(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature
    )
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        rag_service=None
    )
    
    status = await orchestrator.get_agent_status()
    
    print("\nAgent Status:")
    for agent_name, agent_info in status.items():
        if isinstance(agent_info, dict):
            print(f"\n{agent_name}:")
            for key, value in agent_info.items():
                print(f"  {key}: {value}")
        else:
            print(f"{agent_name}: {agent_info}")


async def example_multi_agent_task():
    """Example: Using multiple agents in a hybrid task"""
    
    print("\n" + "="*60)
    print("EXAMPLE 5: Multi-Agent Hybrid Task")
    print("="*60)
    
    # Initialize LLM
    llm_provider = create_llm_provider(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature
    )
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        llm_provider=llm_provider,
        rag_service=None
    )
    
    fashion_content = "Classic gold jewelry and minimalist designs are trending this season."
    
    print("\nRunning hybrid task (trend + customer analysis)...")
    
    result = await orchestrator.handle_multi_agent_task(
        task_type="hybrid",
        content=fashion_content
    )
    
    if result["status"] == "success":
        print(f"\nHybrid Task Results:")
        results = result["results"]
        
        if "trend_analysis" in results:
            print(f"  ✓ Trend Analysis: {results['trend_analysis']['result']['status']}")
        
        if "customer_analysis" in results:
            print(f"  ✓ Customer Analysis: {results['customer_analysis']['result']['status']}")
    else:
        print(f"Error: {result.get('error')}")


async def run_all_examples():
    """Run all agent examples"""
    
    print("\n" + "="*60)
    print("AI AGENTS EXAMPLE USAGE")
    print("="*60)
    
    try:
        # Example 1: Consultant Agent
        await example_consultant_agent()
        
        # Example 2: Analysis Agent
        await example_analysis_agent()
        
        # Example 3: Trend Agent
        await example_trend_agent()
        
        # Example 4: Orchestrator Status
        await example_orchestrator_status()
        
        # Example 5: Multi-Agent Task
        await example_multi_agent_task()
        
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_examples())

