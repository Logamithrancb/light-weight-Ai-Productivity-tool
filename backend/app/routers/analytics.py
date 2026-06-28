from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from backend.app.database import ProductivityDB

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
db = ProductivityDB()

def calculate_productivity_score(completed_items, all_items) -> int:
    if not all_items:
        return 0
        
    # Weight points: High = 3, Medium = 2, Low = 1
    weight_map = {"High": 3, "Medium": 2, "Low": 1}
    
    total_weight = sum(weight_map.get(item.get("priority", "Medium"), 2) for item in all_items)
    completed_weight = sum(weight_map.get(item.get("priority", "Medium"), 2) for item in completed_items)
    
    if total_weight == 0:
        return 0
        
    return int((completed_weight / total_weight) * 100)

@router.get("/summary")
def get_daily_summary():
    """Generates an algorithmic daily productivity summary and statistics."""
    # Get all items
    all_items = db.get_items()
    
    # Filter items created in the last 24 hours
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    
    todays_items = [
        item for item in all_items 
        if datetime.fromisoformat(item["created_at"]) >= day_ago
    ]
    
    todays_completed = [item for item in todays_items if item["status"] == "completed"]
    todays_pending = [item for item in todays_items if item["status"] == "pending"]
    
    completed_count = len(todays_completed)
    total_count = len(todays_items)
    pending_count = len(todays_pending)
    
    completion_rate = int((completed_count / total_count) * 100) if total_count > 0 else 0
    
    # Analyze category distribution
    categories_completed = {}
    categories_total = {}
    for item in todays_items:
        cat = item["category"]
        categories_total[cat] = categories_total.get(cat, 0) + 1
        if item["status"] == "completed":
            categories_completed[cat] = categories_completed.get(cat, 0) + 1
            
    # Find primary focus category
    focus_category = "None"
    max_count = 0
    for cat, count in categories_total.items():
        if count > max_count:
            max_count = count
            focus_category = cat
            
    # Analyze priority distribution
    high_priority_completed = len([i for i in todays_completed if i["priority"] == "High"])
    high_priority_total = len([i for i in todays_items if i["priority"] == "High"])
    high_priority_pending = len([i for i in todays_pending if i["priority"] == "High"])
    
    # Compute productivity score
    productivity_score = calculate_productivity_score(todays_completed, todays_items)
    
    # Algorithmic Summary Text Generation
    summary_text = ""
    if total_count == 0:
        summary_text = "No tasks or notes were recorded today. Enter a task above in natural language to start tracking your productivity!"
    else:
        # Theme introduction
        summary_text += f"Today, you captured {total_count} items with a focus on **{focus_category}**. "
        
        # Completion details
        if completion_rate == 100:
            summary_text += "Outstanding! You completed 100% of today's tasks. Excellent execution. "
        elif completion_rate >= 70:
            summary_text += f"Great job! You achieved a solid completion rate of {completion_rate}%, finishing {completed_count} tasks. "
        elif completion_rate > 0:
            summary_text += f"You have started making progress, completing {completed_count} tasks ({completion_rate}% completion rate). "
        else:
            summary_text += "You haven't checked off any tasks yet today. "
            
        # High Priority alert
        if high_priority_pending > 0:
            summary_text += f"⚠️ **Attention**: You have {high_priority_pending} pending **High Priority** tasks due. We recommend tackling these first to clear critical blocks. "
        elif high_priority_completed > 0 and high_priority_total == high_priority_completed:
            summary_text += "🔥 You successfully cleared all of today's High Priority tasks! "

        # Suggestions
        if pending_count > 0:
            suggested_focus = focus_category if focus_category != "None" else "general tasks"
            summary_text += f"Tomorrow, try focusing on completing the remaining {pending_count} pending tasks in your backlog, particularly in **{suggested_focus}**."
        else:
            summary_text += "Your desk is clean! Take some time to rest or plan your objectives for tomorrow."

    # Letter Grade based on score
    if productivity_score >= 90:
        grade = "A+"
    elif productivity_score >= 80:
        grade = "A"
    elif productivity_score >= 70:
        grade = "B"
    elif productivity_score >= 50:
        grade = "C"
    elif total_count == 0:
        grade = "N/A"
    else:
        grade = "D"
        
    return {
        "summary": summary_text,
        "metrics": {
            "total_tasks": total_count,
            "completed_tasks": completed_count,
            "pending_tasks": pending_count,
            "completion_rate": completion_rate,
            "productivity_score": productivity_score,
            "grade": grade,
            "high_priority_pending": high_priority_pending,
            "focus_category": focus_category
        }
    }

@router.get("/weekly")
def get_weekly_analytics():
    """Generates analytical insights for the past 7 days."""
    all_items = db.get_items()
    
    now = datetime.utcnow()
    # Align to local/UTC days
    seven_days_ago = now - timedelta(days=7)
    
    # Filter items created in the last 7 days
    weekly_items = [
        item for item in all_items 
        if datetime.fromisoformat(item["created_at"]) >= seven_days_ago
    ]
    
    # Calculate completions
    completed = [i for i in weekly_items if i["status"] == "completed"]
    pending = [i for i in weekly_items if i["status"] == "pending"]
    
    weekly_score = calculate_productivity_score(completed, weekly_items)
    
    # Completion count per day of week
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    # Initialize counts
    daily_stats = {day: {"created": 0, "completed": 0} for day in days}
    
    for item in weekly_items:
        dt = datetime.fromisoformat(item["created_at"])
        # dt.weekday() returns 0 for Monday, 6 for Sunday
        day_name = days[dt.weekday()]
        daily_stats[day_name]["created"] += 1
        if item["status"] == "completed":
            daily_stats[day_name]["completed"] += 1
            
    # Flatten daily stats for Recharts
    daily_data = [
        {"day": d, "Created": daily_stats[d]["created"], "Completed": daily_stats[d]["completed"]}
        for d in days
    ]
    
    # Categories distribution
    cat_counts = {}
    for item in weekly_items:
        cat = item["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
    category_data = [
        {"name": cat, "value": count}
        for cat, count in cat_counts.items()
    ]
    
    # Priorities distribution
    prio_counts = {"High": 0, "Medium": 0, "Low": 0}
    for item in weekly_items:
        prio = item["priority"]
        prio_counts[prio] = prio_counts.get(prio, 0) + 1
        
    priority_data = [
        {"name": name, "value": count}
        for name, count in prio_counts.items()
    ]
    
    # Completion rate
    total_count = len(weekly_items)
    comp_rate = int((len(completed) / total_count) * 100) if total_count > 0 else 0
    
    return {
        "score": weekly_score,
        "total_tasks": total_count,
        "completed_tasks": len(completed),
        "pending_tasks": len(pending),
        "completion_rate": comp_rate,
        "daily_trends": daily_data,
        "category_distribution": category_data,
        "priority_distribution": priority_data
    }
