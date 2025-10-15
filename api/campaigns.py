from flask import Blueprint, request, jsonify, send_file
import sys
import os
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.campaign import Campaign
from services.campaign_service import CampaignService

campaigns_bp = Blueprint('campaigns', __name__)

@campaigns_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    session = get_session()
    try:
        campaigns = session.query(Campaign).order_by(Campaign.created_at.desc()).all()
        return jsonify({
            'success': True,
            'campaigns': [c.to_dict() for c in campaigns]
        })
    finally:
        session.close()

@campaigns_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.json
        
        result = CampaignService.create_campaign(
            name=data['name'],
            subject_lines=data['subject_lines'],
            email_body=data['email_body'],
            target_industries=data.get('target_industries', []),
            target_tiers=data.get('target_tiers', []),
            target_sources=data.get('target_sources', []),
            daily_limit=data.get('daily_limit', 30)
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/recipients', methods=['GET'])
def get_recipients(campaign_id):
    """Get campaign recipients"""
    try:
        result = CampaignService.get_campaign_recipients(campaign_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/preview', methods=['GET'])
def preview_campaign(campaign_id):
    """Generate preview CSV"""
    try:
        result = CampaignService.generate_preview_csv(campaign_id)
        
        if not result['success']:
            return jsonify(result), 400
        
        # Return CSV as download
        return send_file(
            io.BytesIO(result['csv_content'].encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'campaign_{campaign_id}_preview.csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/send', methods=['POST'])
def send_campaign(campaign_id):
    """Send campaign batch"""
    try:
        data = request.json or {}
        batch_size = data.get('batch_size')
        preview_mode = data.get('preview_mode', True)
        
        result = CampaignService.send_campaign_batch(
            campaign_id=campaign_id,
            batch_size=batch_size,
            preview_mode=preview_mode
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update campaign"""
    session = get_session()
    try:
        campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        data = request.json
        
        if 'is_active' in data:
            campaign.is_active = 1 if data['is_active'] else 0
        
        session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@campaigns_bp.route('/campaigns/<int:campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete campaign"""
    session = get_session()
    try:
        campaign = session.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        session.delete(campaign)
        session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
