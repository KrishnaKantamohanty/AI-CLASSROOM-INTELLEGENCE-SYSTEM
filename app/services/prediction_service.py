"""Prediction Service — ML-based attendance forecasting."""
try:
    import numpy as np
except ImportError:
    np = None
from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student


class PredictionService:
    """Uses linear regression to predict future attendance trends."""

    @staticmethod
    def predict_attendance_trend(days_ahead=30):
        """Predict attendance rates for the next N days using linear regression."""
        today = date.today()
        lookback = 60  # days of historical data

        # Gather historical daily rates
        start = today - timedelta(days=lookback)
        results = db.session.query(
            Attendance.date,
            func.count(Attendance.id).label('total'),
            func.sum(
                db.case(
                    (Attendance.status.in_(['present', 'late']), 1),
                    else_=0
                )
            ).label('present')
        ).filter(Attendance.date >= start).group_by(Attendance.date).order_by(Attendance.date).all()

        if len(results) < 5:
            # Not enough data for prediction — return flat estimate
            avg_rate = 75.0
            if results:
                total_all = sum(int(r.total) for r in results)
                present_all = sum(int(r.present or 0) for r in results)
                avg_rate = round(present_all / total_all * 100, 1) if total_all > 0 else 75.0

            labels = [(today + timedelta(days=i)).strftime('%b %d') for i in range(1, days_ahead + 1)]
            return {
                'labels': labels,
                'predicted_rates': [avg_rate] * days_ahead,
                'confidence_upper': [min(100, avg_rate + 5)] * days_ahead,
                'confidence_lower': [max(0, avg_rate - 5)] * days_ahead,
                'model': 'flat_estimate'
            }

        # Build X (day index) and y (attendance rate) arrays
        X = []
        y = []
        for i, row in enumerate(results):
            total = int(row.total or 0)
            present = int(row.present or 0)
            if total > 0:
                X.append(i)
                y.append(present / total * 100)

        if np is None:
            # Fallback to simple python math if numpy is missing
            n = len(X)
            x_mean = sum(X) / n
            y_mean = sum(y) / n
            numerator = sum((X[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((X[i] - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean
            
            y_pred_hist = [slope * x + intercept for x in X]
            residuals = [y[i] - y_pred_hist[i] for i in range(n)]
            variance = sum(r**2 for r in residuals) / n if n > 0 else 0
            std_err = variance ** 0.5 if len(residuals) > 2 else 5.0
        else:
            X = np.array(X, dtype=float)
            y = np.array(y, dtype=float)

            # Simple linear regression
            n = len(X)
            x_mean = np.mean(X)
            y_mean = np.mean(y)
            slope = np.sum((X - x_mean) * (y - y_mean)) / np.sum((X - x_mean) ** 2) if np.sum((X - x_mean) ** 2) != 0 else 0
            intercept = y_mean - slope * x_mean

            # Standard error
            y_pred_hist = slope * X + intercept
            residuals = y - y_pred_hist
            std_err = np.std(residuals) if len(residuals) > 2 else 5.0

        # Predict future
        labels = []
        predicted = []
        upper = []
        lower = []

        for i in range(1, days_ahead + 1):
            future_x = n + i
            pred = slope * future_x + intercept
            pred = max(0, min(100, pred))
            predicted.append(round(pred, 1))
            upper.append(round(min(100, pred + 1.96 * std_err), 1))
            lower.append(round(max(0, pred - 1.96 * std_err), 1))
            labels.append((today + timedelta(days=i)).strftime('%b %d'))

        return {
            'labels': labels,
            'predicted_rates': predicted,
            'confidence_upper': upper,
            'confidence_lower': lower,
            'slope': round(slope, 4),
            'model': 'linear_regression'
        }

    @staticmethod
    def predict_student_absence(student_id):
        """Predict probability of a specific student being absent tomorrow."""
        records = Attendance.query.filter_by(student_id=student_id).order_by(
            Attendance.date.desc()
        ).limit(30).all()

        if not records:
            return {'probability': 0.5, 'trend': 'unknown'}

        # Count recent absences
        total = len(records)
        absences = sum(1 for r in records if r.status == 'absent')
        absence_rate = absences / total

        # Weight recent records more heavily
        recent_5 = records[:5]
        recent_absences = sum(1 for r in recent_5 if r.status == 'absent')
        recent_rate = recent_absences / len(recent_5)

        # Blended probability
        prob = 0.6 * recent_rate + 0.4 * absence_rate

        trend = 'improving' if recent_rate < absence_rate else 'declining' if recent_rate > absence_rate else 'stable'

        return {
            'probability': round(prob * 100, 1),
            'trend': trend,
            'recent_absence_rate': round(recent_rate * 100, 1),
            'overall_absence_rate': round(absence_rate * 100, 1)
        }
