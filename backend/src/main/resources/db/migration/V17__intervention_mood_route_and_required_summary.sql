UPDATE intervention_materials
SET route_path = '/healing?tab=diary'
WHERE code = 'mood-diary';

UPDATE intervention_publish_items
SET route_path = '/healing?tab=diary'
WHERE item_type = 'mood' AND route_path = '/record';
