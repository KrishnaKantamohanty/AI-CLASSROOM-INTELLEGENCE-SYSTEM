"""Smart Insight Engine — generates natural language AI insights automatically."""
from datetime import datetime, timedelta, date
from sqlalchemy import func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.classroom import Classroom
from app.models.ai_insight import AIInsight


class InsightEngine:
    """Generates AI-powered natural language insights about classroom performance."""

    @staticmethod
    def generate_all_insights():
        """Run all insight generators and store new insights."""
        insights = []
        insights.extend(InsightEngine._attendance_trend_insights())
        insights.extend(InsightEngine._day_pattern_insights())
        insights.extend(InsightEngine._risk_insights())
        insights.extend(InsightEngine._occupancy_insights())
        insights.extend(InsightEngine._improvement_insights())

        # Store in database (clear old insights first)
        AIInsight.query.filter_by(is_active=True).update({'is_active': False})

        for ins in insights:
            ai_insight = AIInsight(
                insight_text=ins['text'],
                category=ins['category'],
                severity=ins['severity'],
                icon=ins.get('icon', 'bi-lightbulb'),
                is_active=True,
                generated_at=datetime.utcnow()
            )
            db.session.add(ai_insight)

        db.session.commit()
        return insights

    @staticmethod
    def _attendance_trend_insights():
        """Compare this week's attendance to last week."""
        insights = []
        today = date.today()

        # This week
        week_start = today - timedelta(days=today.weekday())
        this_week_total = Attendance.query.filter(Attendance.date >= week_start).count()
        this_week_present = Attendance.query.filter(
            Attendance.date >= week_start,
            Attendance.status.in_(['present', 'late'])
        ).count()

        # Last week
        last_week_start = week_start - timedelta(days=7)
        last_week_total = Attendance.query.filter(
            Attendance.date >= last_week_start,
            Attendance.date < week_start
        ).count()
        last_week_present = Attendance.query.filter(
            Attendance.date >= last_week_start,
            Attendance.date < week_start,
            Attendance.status.in_(['present', 'late'])
        ).count()

        this_rate = (this_week_present / this_week_total * 100) if this_week_total > 0 else 0
        last_rate = (last_week_present / last_week_total * 100) if last_week_total > 0 else 0

        if last_rate > 0:
            change = this_rate - last_rate
            if change > 0:
                insights.append({
                    'text': f'Attendance increased by {abs(change):.1f}% compared to last week. Great progress!',
                    'category': 'attendance',
                    'severity': 'success',
                    'icon': 'bi-graph-up-arrow'
                })
            elif change < -5:
                insights.append({
                    'text': f'Attendance dropped by {abs(change):.1f}% compared to last week. Attention needed.',
                    'category': 'attendance',
                    'severity': 'warning',
                    'icon': 'bi-graph-down-arrow'
                })

        return insights

    @staticmethod
    def _day_pattern_insights():
        """Find the best and worst attendance days."""
        insights = []

        results = db.session.query(
            func.strftime('%w', Attendance.date).label('dow'),
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).group_by('dow').all()

        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_rates = {}
        for row in results:
            dow = int(row.dow)
            total = int(row.total or 0)
            present = int(row.present or 0)
            if total > 0:
                day_rates[dow] = round(present / total * 100, 1)

        if day_rates:
            best_day = max(day_rates, key=day_rates.get)
            worst_day = min(day_rates, key=day_rates.get)

            insights.append({
                'text': f'{day_names[best_day]} classes have the highest attendance at {day_rates[best_day]}%.',
                'category': 'performance',
                'severity': 'info',
                'icon': 'bi-calendar-check'
            })

            if day_rates[best_day] - day_rates[worst_day] > 10:
                insights.append({
                    'text': f'{day_names[worst_day]} has the lowest attendance ({day_rates[worst_day]}%). Consider scheduling key sessions on other days.',
                    'category': 'performance',
                    'severity': 'warning',
                    'icon': 'bi-calendar-x'
                })

        return insights

    @staticmethod
    def _risk_insights():
        """Generate insights about at-risk students."""
        insights = []
        students = Student.query.filter_by(is_active=True).all()

        at_risk_count = sum(1 for s in students if s.attendance_percentage < 75)
        critical_count = sum(1 for s in students if s.attendance_percentage < 50)

        if at_risk_count > 0:
            insights.append({
                'text': f'{at_risk_count} students are at risk due to low attendance (below 75%). Immediate action recommended.',
                'category': 'risk',
                'severity': 'warning' if critical_count == 0 else 'critical',
                'icon': 'bi-exclamation-triangle'
            })

        if critical_count > 0:
            insights.append({
                'text': f'{critical_count} students have critically low attendance (below 50%). Contact guardians immediately.',
                'category': 'risk',
                'severity': 'critical',
                'icon': 'bi-exclamation-octagon'
            })

        return insights

    @staticmethod
    def _occupancy_insights():
        """Analyze classroom utilization."""
        insights = []
        classrooms = Classroom.query.filter_by(is_active=True).all()

        for cr in classrooms:
            pct = cr.occupancy_percentage
            if 0 < pct < 50:
                insights.append({
                    'text': f'Classroom {cr.name} utilization is only {pct}%. Schedule optimization recommended.',
                    'category': 'occupancy',
                    'severity': 'info',
                    'icon': 'bi-building'
                })
            elif pct > 95:
                insights.append({
                    'text': f'Classroom {cr.name} is near full capacity ({pct}%). Consider additional sections.',
                    'category': 'occupancy',
                    'severity': 'warning',
                    'icon': 'bi-building-exclamation'
                })

        return insights

    @staticmethod
    def _improvement_insights():
        """Detect improved attendance trends."""
        insights = []
        today = date.today()

        # This month vs last month
        month_start = today.replace(day=1)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        this_month_total = Attendance.query.filter(Attendance.date >= month_start).count()
        this_month_present = Attendance.query.filter(
            Attendance.date >= month_start,
            Attendance.status.in_(['present', 'late'])
        ).count()

        last_month_total = Attendance.query.filter(
            Attendance.date >= last_month_start,
            Attendance.date < month_start
        ).count()
        last_month_present = Attendance.query.filter(
            Attendance.date >= last_month_start,
            Attendance.date < month_start,
            Attendance.status.in_(['present', 'late'])
        ).count()

        this_rate = (this_month_present / this_month_total * 100) if this_month_total > 0 else 0
        last_rate = (last_month_present / last_month_total * 100) if last_month_total > 0 else 0

        if last_rate > 0 and this_rate > last_rate:
            change = this_rate - last_rate
            insights.append({
                'text': f'Attendance has improved by {change:.1f}% over the last month. Keep up the excellent work!',
                'category': 'performance',
                'severity': 'success',
                'icon': 'bi-trophy'
            })

        return insights

    @staticmethod
    def get_active_insights(limit=10):
        """Retrieve active insights for display."""
        return AIInsight.query.filter_by(is_active=True).order_by(
            AIInsight.generated_at.desc()
        ).limit(limit).all()
