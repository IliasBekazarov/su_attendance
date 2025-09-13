from django import template

register = template.Library()

@register.filter
def filter_schedule(schedules, args):
    """
    Schedules'ти group_id жана period (пара) боюнча фильтрлейт.
    args - бул group_id жана period'ти камтыган строка (мисалы, "1,2").
    Эгер дал келген schedule табылса, аны кайтарат, болбосо None.
    """
    try:
        group_id, period = map(int, args.split(','))  # args'ти бөлүп алуу
        return schedules.filter(group_id=group_id, period=period).first()
    except (ValueError, AttributeError):
        return None