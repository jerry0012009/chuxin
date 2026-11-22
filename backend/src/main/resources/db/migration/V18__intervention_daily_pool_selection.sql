UPDATE intervention_plan_template_items
SET required = TRUE,
    frequency_type = 'daily';

UPDATE intervention_publish_items
SET required = TRUE,
    frequency_type = 'daily';
