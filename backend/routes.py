"""FastAPI routes for AI Jewelry Consultation System"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ConsultationRequest,
    ConsultationResponse,
    GirlfriendChatRequest,
    GirlfriendChatResponse,
    TasteDetectionRequest,
    TasteDetectionResponse,
    CustomerProfileResponse,
    CustomerPreferenceUpdate,
    CustomerPreferenceUpdateResponse,
    AnalysisReportResponse,
    TrendAnalysisRequest,
    TrendReportResponse,
    ProductSearchRequest,
    ProductSearchResponse,
    ProductInfo,
    HealthResponse,
    ErrorResponse
)
from backend.dependencies import (
    get_orchestrator,
    get_preference_repository,
    get_product_repository,
    get_qdrant_service,
    check_database_health,
    check_qdrant_health
)
from agents.orchestrator import AgentOrchestrator
from database.repositories import CustomerPreferenceRepository, JewelryProductRepository
from database.models import CustomerPreference
from rag.qdrant_service import QdrantService
from config import settings
from utils.logging import get_logger


logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["api"])


@router.post(
    "/orchestrator/{user_id}",
    response_model=ChatResponse
)
async def orchestrator(
        user_id: str,
        request: ChatRequest,
        orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Обработка сообщения пользователя"""
    try:
        logger.info(f"Orchestrator request from user {user_id}")
        result = await orchestrator.handle_user_message(
            user_id=user_id,
            message=request.message,
            conversation_history=request.conversation_history,
            explicit_task_type=request.explicit_task_type
        )

        return ChatResponse(
            status=result.get("status", "success"),
            task_type=result.get("task_type"),
            response=result.get("result"),
            error=result.get("error"),
            completed_agents=result.get("completed_agents", [])
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        return ChatResponse(
            status="error",
            error=str(e),
            task_type=None,
        )


# Consultation endpoints
@router.post(
    "/consultation/{user_id}",
    response_model=ConsultationResponse,
    summary="User consultation with AI agent",
    description="Get personalized jewelry recommendations and consultation"
)
async def consultation(
    user_id: str,
    request: ConsultationRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Handle user consultation request

    Args:
        user_id: User identifier
        request: Consultation request with message and optional history
        orchestrator: Agent orchestrator dependency

    Returns:
        ConsultationResponse with recommendations and agent response
    """
    try:
        logger.info(f"Consultation request from user {user_id}")

        # Process consultation through orchestrator
        result = await orchestrator.handle_user_orchestrator(
            user_id=user_id,
            message=request.message,
            conversation_history=request.conversation_history
        )

        # Extract data from result
        if result.get("status") == "success":
            agent_result = result.get("result", {})

            return ConsultationResponse(
                status="success",
                agent="consultant",
                products=agent_result.get("products"),
                response=agent_result.get("response"),
                recommendations=agent_result.get("recommendations"),
                extracted_preferences=agent_result.get(
                    "extracted_preferences"),
                questions_for_user=agent_result.get("questions_for_user")
            )
        else:
            return ConsultationResponse(
                status="error",
                agent="consultant",
                error=result.get("error", "Unknown error occurred")
            )

    except Exception as e:
        logger.error(
            f"Consultation error for user {user_id}: {e}", exc_info=True)
        return ConsultationResponse(
            status="error",
            agent="consultant",
            error=str(e)
        )


@router.post(
    "/girlfriend/{user_id}",
    response_model=GirlfriendChatResponse,
    summary="Чат с girlfriend-агентом",
    description="Тёплый дружеский чат + гороскопы (через публичное API)"
)
async def girlfriend_chat(
    user_id: str,
    request: GirlfriendChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """Chat endpoint for the girlfriend agent."""
    try:
        logger.info(f"Girlfriend chat request from user {user_id}")

        result = await orchestrator.run_girlfriend_answer(
            user_id=user_id,
            message=request.message,
            conversation_history=request.conversation_history,
            zodiac_sign=request.zodiac_sign,
        )

        if result.get("status") == "success":
            agent_block = (result.get("result") or {}).get("girlfriend") or {}
            return GirlfriendChatResponse(
                status="success",
                agent="girlfriend",
                response=agent_block.get("response"),
                zodiac_sign=agent_block.get("zodiac_sign"),
            )

        return GirlfriendChatResponse(
            status="error",
            agent="girlfriend",
            error=result.get("error", "Unknown error occurred")
        )

    except Exception as e:
        logger.error(
            f"Girlfriend chat error for user {user_id}: {e}", exc_info=True)
        return GirlfriendChatResponse(
            status="error",
            agent="girlfriend",
            error=str(e)
        )


# Taste detection endpoints
@router.post(
    "/taste/{user_id}",
    response_model=TasteDetectionResponse,
    summary="Jewelry taste detection",
    description="Detect user jewelry preferences through structured questions"
)
async def taste_detection(
    user_id: str,
    request: TasteDetectionRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Handle taste detection request

    Args:
        user_id: User identifier
        request: Taste detection request with message and optional state
        orchestrator: Agent orchestrator dependency

    Returns:
        TasteDetectionResponse with taste analysis results
    """
    try:
        logger.info(f"Taste detection request from user {user_id}")

        result = await orchestrator.run_taste_detection(
            user_id=user_id,
            message=request.message,
            conversation_history=request.conversation_history,
            current_question_index=request.current_question_index,
            answers=request.answers
        )

        # Extract data from result
        if result.get("status") == "success":
            agent_result = result.get("result", {})

            return TasteDetectionResponse(
                status="success",
                agent="taste",
                response=agent_result.get("response"),
                current_question_index=agent_result.get(
                    "current_question_index"),
                answers=agent_result.get("answers"),
                jewelry_profile=agent_result.get("jewelry_profile")
            )
        else:
            return TasteDetectionResponse(
                status="error",
                agent="taste",
                error=result.get("error", "Unknown error occurred")
            )

    except Exception as e:
        logger.error(
            f"Taste detection error for user {user_id}: {e}", exc_info=True)
        return TasteDetectionResponse(
            status="error",
            agent="taste",
            error=str(e)
        )


# Customer profile endpoints
@router.get(
    "/customer/{user_id}/profile",
    response_model=CustomerProfileResponse,
    summary="Get customer profile",
    description="Retrieve customer preferences and profile information"
)
async def get_customer_profile(
    user_id: str,
    preference_repo: CustomerPreferenceRepository = Depends(
        get_preference_repository)
):
    """
    Get customer profile by user ID

    Args:
        user_id: User identifier
        preference_repo: Customer preference repository dependency

    Returns:
        CustomerProfileResponse with user preferences
    """
    try:
        logger.info(f"Fetching profile for user {user_id}")

        profile = await preference_repo.get(user_id)

        if profile is None:
            # Return empty profile for new user
            return CustomerProfileResponse(
                user_id=user_id,
                style_preference=None,
                budget_min=None,
                budget_max=None,
                preferred_materials=None,
                skin_tone=None,
                occasion_types=None,
                consultation_history=[]
            )

        return CustomerProfileResponse.model_validate(profile)

    except Exception as e:
        logger.error(
            f"Error fetching profile for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer profile: {str(e)}"
        )


@router.put(
    "/customer/{user_id}/preferences",
    response_model=CustomerPreferenceUpdateResponse,
    summary="Update customer preferences",
    description="Update or create customer preferences"
)
async def update_customer_preferences(
    user_id: str,
    preferences: CustomerPreferenceUpdate,
    preference_repo: CustomerPreferenceRepository = Depends(
        get_preference_repository)
):
    """
    Update customer preferences

    Args:
        user_id: User identifier
        preferences: Preference updates
        preference_repo: Customer preference repository dependency

    Returns:
        CustomerPreferenceUpdateResponse with status
    """
    try:
        logger.info(f"Updating preferences for user {user_id}")

        # Get existing profile or create new
        existing = await preference_repo.get(user_id)

        # Prepare update data
        update_data = preferences.model_dump(exclude_unset=True)
        updated_fields = list(update_data.keys())

        if existing:
            # Update existing profile
            for key, value in update_data.items():
                setattr(existing, key, value)
            updated = await preference_repo.update(user_id, update_data)
        else:
            # Create new profile
            new_preference = CustomerPreference(
                user_id=user_id,
                **update_data
            )
            updated = await preference_repo.create(new_preference)

        return CustomerPreferenceUpdateResponse(
            status="success",
            user_id=user_id,
            updated_fields=updated_fields,
            message=f"Successfully updated {len(updated_fields)} fields"
        )

    except Exception as e:
        logger.error(
            f"Error updating preferences for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


# Analysis endpoints
@router.post(
    "/analysis/customer",
    response_model=AnalysisReportResponse,
    summary="Run customer analysis",
    description="Analyze customer preferences and generate insights"
)
async def customer_analysis(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Run customer analysis via AnalysisAgent

    Args:
        orchestrator: Agent orchestrator dependency

    Returns:
        AnalysisReportResponse with analysis results
    """
    try:
        logger.info("Running customer analysis")

        result = await orchestrator.run_customer_analysis()

        if result.get("status") == "success":
            agent_result = result.get("result", {})

            return AnalysisReportResponse(
                status="success",
                agent="analysis",
                report=agent_result.get("report"),
                # consultation_records=agent_result.get("consultation_records"),
                # consultation_stats=agent_result.get("consultation_stats"),
                customer_segments=agent_result.get("customer_segments"),
                patterns=agent_result.get("patterns"),
                demand_forecast=agent_result.get("demand_forecast"),
                # insights=agent_result.get("insights")
            )
        else:
            return AnalysisReportResponse(
                status="error",
                agent="analysis",
                error=result.get("error", "Unknown error occurred")
            )

    except Exception as e:
        logger.error(f"Customer analysis error: {e}", exc_info=True)
        return AnalysisReportResponse(
            status="error",
            agent="analysis",
            error=str(e)
        )


@router.post(
    "/analysis/trends",
    response_model=TrendReportResponse,
    summary="Run trend analysis",
    description="Analyze fashion trends from journal content"
)
async def trend_analysis(
    request: TrendAnalysisRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Run trend analysis via TrendAgent

    Args:
        request: Trend analysis request with content
        orchestrator: Agent orchestrator dependency

    Returns:
        TrendReportResponse with trend analysis results
    """
    try:
        logger.info(
            f"Running trend analysis on content from {request.source or 'unknown source'}")

        result = await orchestrator.run_trend_analysis(request.content)

        if result.get("status") == "success":
            agent_result = result.get("result", {})

            return TrendReportResponse(
                status="success",
                agent="trend",
                keywords=agent_result.get("extracted_keywords"),
                trends=agent_result.get("trends"),
                mentioned_products=agent_result.get("emerging_trends"),
                trend_scores=agent_result.get("trend_scores"),
                recommendations=agent_result.get("recommendations"),
                report=agent_result.get("report")
            )
        else:
            return TrendReportResponse(
                status="error",
                agent="trend",
                error=result.get("error", "Unknown error occurred")
            )

    except Exception as e:
        logger.error(f" r: {e}", exc_info=True)
        return TrendReportResponse(
            status="error",
            agent="trend",
            error=str(e)
        )


# Product search endpoints
@router.post(
    "/products/search",
    response_model=ProductSearchResponse,
    summary="Search products",
    description="Semantic search for jewelry products using RAG"
)
async def search_products(
    request: ProductSearchRequest,
    qdrant_service: QdrantService = Depends(get_qdrant_service),
    product_repo: JewelryProductRepository = Depends(get_product_repository)
):
    """
    Search for products using semantic search

    Args:
        request: Product search request
        qdrant_service: Qdrant service dependency
        product_repo: Product repository dependency

    Returns:
        ProductSearchResponse with found products
    """
    try:
        logger.info(f"Product search: {request.query}")

        if qdrant_service is None:
            # Fallback to database search if Qdrant unavailable
            logger.warning("Qdrant unavailable, using database fallback")
            products = await product_repo.search_by_text(request.query, limit=request.limit)

            product_list = [
                ProductInfo(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    category=p.category,
                    material=p.material,
                    weight=p.weight,
                    price=p.price,
                    design_details=p.design_details,
                    images=p.images,
                    stock_count=p.stock_count,
                    score=None
                )
                for p in products
            ]

            return ProductSearchResponse(
                status="success",
                query=request.query,
                products=product_list,
                total_found=len(product_list)
            )

        # Use Qdrant for semantic search
        results = await qdrant_service.search(
            query=request.query,
            limit=request.limit,
            score_threshold=0.5
        )

        product_list = []
        for result in results:
            payload = result.get("payload", {})
            product_list.append(ProductInfo(
                id=payload.get("id", ""),
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                category=payload.get("category", ""),
                material=payload.get("material", ""),
                weight=payload.get("weight", 0.0),
                price=payload.get("price", 0.0),
                design_details=payload.get("design_details"),
                images=payload.get("images"),
                stock_count=payload.get("stock_count", 0),
                score=result.get("score")
            ))

        return ProductSearchResponse(
            status="success",
            query=request.query,
            products=product_list,
            total_found=len(product_list)
        )

    except Exception as e:
        logger.error(f"Product search error: {e}", exc_info=True)
        return ProductSearchResponse(
            status="error",
            query=request.query,
            products=[],
            total_found=0,
            error=str(e)
        )


# Health check endpoint
@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check system health and component status"
)
async def health_check(
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    qdrant_service: QdrantService = Depends(get_qdrant_service)
):
    """
    Comprehensive health check

    Args:
        orchestrator: Agent orchestrator dependency
        qdrant_service: Qdrant service dependency

    Returns:
        HealthResponse with system status
    """
    try:
        # Check database
        db_healthy = await check_database_health()

        # Check Qdrant
        qdrant_healthy = await check_qdrant_health(qdrant_service)

        # Get agent status
        agents_status = await orchestrator.get_agent_status()

        overall_status = "healthy" if db_healthy else "unhealthy"

        return HealthResponse(
            status=overall_status,
            provider=settings.llm_provider,
            model=settings.llm_model,
            database_connected=db_healthy,
            qdrant_connected=qdrant_healthy,
            agents_status=agents_status
        )

    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            provider=settings.llm_provider,
            model=settings.llm_model,
            database_connected=False,
            qdrant_connected=False,
            agents_status=None
        )
