SET @scale_surveys_sort_order_exists = (
  SELECT COUNT(*)
  FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'scale_surveys'
    AND COLUMN_NAME = 'sort_order'
);

SET @scale_surveys_sort_order_sql = IF(
  @scale_surveys_sort_order_exists = 0,
  'ALTER TABLE scale_surveys ADD COLUMN sort_order INT NULL DEFAULT NULL AFTER self_test_enabled',
  'SELECT 1'
);

PREPARE scale_surveys_sort_order_stmt FROM @scale_surveys_sort_order_sql;
EXECUTE scale_surveys_sort_order_stmt;
DEALLOCATE PREPARE scale_surveys_sort_order_stmt;
