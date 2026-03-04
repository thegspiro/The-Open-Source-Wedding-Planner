from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Wedding, Ceremony, CeremonyTimelineItem, CeremonyReading
from datetime import datetime

ceremony_bp = Blueprint('ceremony', __name__, url_prefix='/wedding/<int:wedding_id>/ceremony')

@ceremony_bp.route('/')
def view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    ceremony = wedding.ceremony
    
    if not ceremony:
        ceremony = Ceremony(wedding_id=wedding_id)
        db.session.add(ceremony)
        db.session.commit()
    
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order)
    readings = sorted(ceremony.readings, key=lambda x: x.order or 999)
    
    return render_template('ceremony/view.html', wedding=wedding, ceremony=ceremony,
                         timeline_items=timeline_items, readings=readings)

@ceremony_bp.route('/edit', methods=['GET', 'POST'])
def edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    ceremony = wedding.ceremony
    
    if request.method == 'POST':
        # Venue details
        ceremony.venue_name = request.form.get('venue_name')
        ceremony.venue_address = request.form.get('venue_address')
        ceremony.venue_contact = request.form.get('venue_contact')
        ceremony.venue_phone = request.form.get('venue_phone')
        
        # Timing
        if request.form.get('start_time'):
            ceremony.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        ceremony.duration_minutes = request.form.get('duration_minutes', type=int)
        
        # Officiant
        ceremony.officiant_name = request.form.get('officiant_name')
        ceremony.officiant_contact = request.form.get('officiant_contact')
        ceremony.officiant_phone = request.form.get('officiant_phone')
        ceremony.officiant_type = request.form.get('officiant_type')
        
        # Style
        ceremony.ceremony_style = request.form.get('ceremony_style')
        ceremony.vow_type = request.form.get('vow_type')
        
        # Music
        ceremony.processional_song = request.form.get('processional_song')
        ceremony.recessional_song = request.form.get('recessional_song')
        ceremony.unity_ceremony_song = request.form.get('unity_ceremony_song')
        
        # Unity ceremony
        ceremony.has_unity_ceremony = request.form.get('has_unity_ceremony') == 'on'
        ceremony.unity_ceremony_type = request.form.get('unity_ceremony_type')
        ceremony.has_special_readings = request.form.get('has_special_readings') == 'on'
        
        db.session.commit()
        flash('Ceremony details updated!', 'success')
        return redirect(url_for('ceremony.view', wedding_id=wedding_id))
    
    return render_template('ceremony/edit.html', wedding=wedding, ceremony=ceremony)

@ceremony_bp.route('/timeline/add', methods=['POST'])
def add_timeline_item(wedding_id):
    ceremony = Wedding.query.get_or_404(wedding_id).ceremony
    
    item = CeremonyTimelineItem(
        ceremony_id=ceremony.id,
        order=request.form.get('order', type=int),
        item_name=request.form.get('item_name'),
        duration_seconds=request.form.get('duration_seconds', type=int),
        description=request.form.get('description'),
        participants=request.form.get('participants')
    )
    
    db.session.add(item)
    db.session.commit()
    flash('Timeline item added!', 'success')
    return redirect(url_for('ceremony.view', wedding_id=wedding_id))

@ceremony_bp.route('/timeline/<int:item_id>/delete', methods=['POST'])
def delete_timeline_item(wedding_id, item_id):
    item = CeremonyTimelineItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Timeline item deleted!', 'success')
    return redirect(url_for('ceremony.view', wedding_id=wedding_id))

@ceremony_bp.route('/reading/add', methods=['POST'])
def add_reading(wedding_id):
    ceremony = Wedding.query.get_or_404(wedding_id).ceremony
    
    reading = CeremonyReading(
        ceremony_id=ceremony.id,
        title=request.form.get('title'),
        author=request.form.get('author'),
        reader_name=request.form.get('reader_name'),
        text_content=request.form.get('text_content'),
        order=request.form.get('order', type=int)
    )
    
    db.session.add(reading)
    db.session.commit()
    flash('Reading added!', 'success')
    return redirect(url_for('ceremony.view', wedding_id=wedding_id))

@ceremony_bp.route('/reading/<int:reading_id>/delete', methods=['POST'])
def delete_reading(wedding_id, reading_id):
    reading = CeremonyReading.query.get_or_404(reading_id)
    db.session.delete(reading)
    db.session.commit()
    flash('Reading deleted!', 'success')
    return redirect(url_for('ceremony.view', wedding_id=wedding_id))
