from flask import Blueprint, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import JOB_CATEGORIES, CONTACT_STATUSES

filters_bp = Blueprint('filters', __name__)

@filters_bp.route('/filters/options', methods=['GET'])
def get_filter_options():
    """Get all available filter options"""
    return jsonify({
        'success': True,
        'job_categories': JOB_CATEGORIES,
        'statuses': CONTACT_STATUSES
    })
