from django import template
from datetime import time

register = template.Library()

@register.filter
def filter_schedule(schedules, args):
    """
    Schedules'ти group_id жана period (пара) боюнча фильтрлейт.
    args - бул "group_id,period" форматы
    """
    try:
        if isinstance(args, str) and ',' in args:
            group_id, period = args.split(',')
        else:
            return None
            
        group_id = int(group_id)
        period = int(period)
        
        # Period боюнча убакыт range'ин аныктоо
        period_times = {
            1: time(9, 0),   # 09:00
            2: time(10, 45), # 10:45  
            3: time(13, 0),  # 13:00
            4: time(15, 0),  # 15:00
            5: time(16, 30), # 16:30
        }
        
        if period in period_times:
            start_time = period_times[period]
            return schedules.filter(
                group_id=group_id,
                start_time=start_time
            ).first()
        return None
    except (ValueError, AttributeError, TypeError, IndexError):
        return None

@register.filter
def get_item(dictionary, key):
    """Dictionary'den key боюнча маанин алуу"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter  
def get_schedules_for_day_period(schedule_matrix, args):
    """
    schedule_matrix'тен белгилүү күн жана период үчүн schedules'ти алуу
    args форматы: "day_code,period_name"
    """
    try:
        if not isinstance(args, str) or ',' not in args:
            return []
            
        day_code, period_name = args.split(',', 1)
        
        if isinstance(schedule_matrix, dict):
            day_data = schedule_matrix.get(day_code, {})
            if isinstance(day_data, dict):
                period_data = day_data.get(period_name, {})
                if isinstance(period_data, dict):
                    return period_data.get('schedules', [])
        
        return []
    except (ValueError, TypeError):
        return []

@register.filter
def get_day_name(day_value):
    """
    Күндөрдүн санын ата-жөнүнө айландырат
    """
    if not day_value:
        return 'Белгисиз күн'
    
    try:
        day_value = int(day_value)
    except (ValueError, TypeError):
        return f'Күн {day_value}'
    
    day_names = {
        1: 'Дүйшөмбү',
        2: 'Шейшемби', 
        3: 'Шаршемби',
        4: 'Бейшемби',
        5: 'Жума',
        6: 'Ишемби',
        0: 'Жекшемби',  # Python datetime жекшембини 0 деп алат
        7: 'Жекшемби'   # Кээ бир системалар 7 деп алышат
    }
    return day_names.get(day_value, f'Күн {day_value}')