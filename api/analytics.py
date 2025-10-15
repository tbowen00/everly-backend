from flask import Blueprint, request, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get dashboard statistics"""
    try:
        stats = AnalyticsService.get_dashboard_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/industry-performance', methods=['GET'])
def get_industry_performance():
    """Get performance by industry"""
    try:
        performance = AnalyticsService.get_industry_performance()
        return jsonify({
            'success': True,
            'performance': performance
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/analytics/source-performance', methods=['GET'])
def get_source_performance():
    """Get performance by source (Google vs Yelp)"""
    try:
        performance = AnalyticsService.get_source_performance()
        return jsonify({
            'success': True,
            'performance': performance
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
