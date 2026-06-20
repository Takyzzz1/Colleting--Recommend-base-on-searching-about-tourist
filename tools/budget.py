"""Budget calculator tool — pure calculation, no external API calls."""
from langchain_core.tools import tool


@tool
def calculate_budget(
    hotel_per_night: float,
    nights: int,
    flights: float,
    food_per_day: float,
    activities: float,
    transport: float,
    shopping: float,
    total_budget: float,
) -> dict:
    """Calculate and break down travel expenses. Returns total, breakdown, remaining budget and suggestions."""
    hotel_total = hotel_per_night * nights
    food_total = food_per_day * nights
    total = hotel_total + flights + food_total + activities + transport + shopping
    remaining = total_budget - total

    breakdown = {
        "hotel": hotel_total,
        "flights": flights,
        "food": food_total,
        "activities": activities,
        "transport": transport,
        "shopping": shopping,
    }

    suggestions = []
    if remaining < 0:
        over = abs(remaining)
        suggestions = [
            f"Ngân sách vượt {over:,.0f} VND. Gợi ý tiết kiệm:",
            f"- Giảm chi phí khách sạn: thử homestay hoặc hostel (~{hotel_per_night * 0.4:,.0f} VND/đêm thay vì {hotel_per_night:,.0f} VND/đêm)",
            f"- Ăn tại quán bình dân thay vì nhà hàng (~{food_per_day * 0.5:,.0f} VND/ngày)",
            f"- Giảm mua sắm hoặc hoạt động tự chọn",
        ]

    return {
        "total": total,
        "breakdown": breakdown,
        "remaining": remaining,
        "is_over_budget": remaining < 0,
        "suggestions": suggestions,
    }
