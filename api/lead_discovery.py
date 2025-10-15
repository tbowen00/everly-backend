from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_session
from models.lead_discovery import LeadDiscovery
from services.lead_discovery_service import LeadDiscoveryService
from config import GOOGLE_PLACES_API_KEY, YELP_API_KEY

lead_discovery_bp = Blueprint('lead_discovery', __name__)

job_progress = {}

def update_job_progress(job_id, message, step=None, total=None):
    """Update job progress that can be polled by frontend"""
    job_progress[job_id] = {
        'message': message,
        'step': step,
        'total': total,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }

@lead_discovery_bp.route('/lead-discovery/jobs', methods=['GET'])
def get_jobs():
    """Get all discovery jobs"""
    session = get_session()
    try:
        jobs = session.query(LeadDiscovery).order_by(LeadDiscovery.created_at.desc()).all()
        jobs_data = []
        for job in jobs:
            job_dict = job.to_dict()
            if job.id in job_progress:
                job_dict['progress'] = job_progress[job.id]
            jobs_data.append(job_dict)
        return jsonify({
            'success': True,
            'jobs': jobs_data
        })
    finally:
        session.close()

@lead_discovery_bp.route('/lead-discovery/jobs/<int:job_id>/progress', methods=['GET'])
def get_job_progress(job_id):
    """Get current progress of a running job"""
    return jsonify({
        'success': True,
        'progress': job_progress.get(job_id, {})
    })

@lead_discovery_bp.route('/lead-discovery/jobs', methods=['POST'])
def create_job():
    """Create a new discovery job"""
    try:
        data = request.json
        
        service = LeadDiscoveryService(GOOGLE_PLACES_API_KEY, YELP_API_KEY)
        job = service.create_discovery_job(
            job_name=data['job_name'],
            source=data['source'],
            location=data['location'],
            radius_miles=data.get('radius_miles', 10),
            industries=data.get('industries', [])
        )
        
        return jsonify({
            'success': True,
            'job': job
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@lead_discovery_bp.route('/lead-discovery/jobs/<int:job_id>/run', methods=['POST'])
def run_job(job_id):
    """Execute a discovery job"""
    try:
        service = LeadDiscoveryService(
            GOOGLE_PLACES_API_KEY, 
            YELP_API_KEY,
            progress_callback=lambda msg, step=None, total=None: update_job_progress(job_id, msg, step, total)
        )
        result = service.run_discovery_job(job_id)
        
        if job_id in job_progress:
            del job_progress[job_id]
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ ERROR in run_job API: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        
        if job_id in job_progress:
            del job_progress[job_id]
        
        return jsonify({'success': False, 'error': str(e)}), 500

@lead_discovery_bp.route('/lead-discovery/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a discovery job (even if running)"""
    session = get_session()
    try:
        job = session.query(LeadDiscovery).filter(LeadDiscovery.id == job_id).first()
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        # Clear progress if exists
        if job_id in job_progress:
            del job_progress[job_id]
        
        session.delete(job)
        session.commit()
        
        print(f"🗑️  Deleted job: {job.job_name} (was: {job.status})", flush=True)
        
        return jsonify({'success': True})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@lead_discovery_bp.route('/lead-discovery/enrich', methods=['POST'])
def enrich_leads():
    """Bulk enrich unenriched leads"""
    try:
        batch_size = request.json.get('batch_size', 10) if request.json else 10
        
        service = LeadDiscoveryService()
        result = service.bulk_enrich(batch_size)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@lead_discovery_bp.route('/lead-discovery/import', methods=['POST'])
def import_lead():
    """Manually import a single lead"""
    try:
        data = request.json
        
        service = LeadDiscoveryService()
        result = service.import_lead(data)
        
        return jsonify({
            'success': result['imported'],
            'result': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
