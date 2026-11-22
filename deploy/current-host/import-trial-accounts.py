"""Convert a private export on stdin to a transactional, insert-only SQL stream."""
import json
import re
import sys
import uuid

COLUMNS = {
    'users': ('id username email password_hash role status last_login_at created_at updated_at').split(),
    'profiles': ('id username email role department_id phone wechat avatar_url full_name gender '
                 'birth_date bio background_url selected_background created_at updated_at').split(),
}


def literal(value):
    if value is None:
        return 'NULL'
    if not isinstance(value, str):
        raise ValueError('Unexpected export value type')
    return f"CONVERT(X'{value.encode('utf8').hex()}' USING utf8mb4)"


rows = [json.loads(line) for line in sys.stdin if line.strip()]
if len(rows) != int(sys.argv[1]):
    raise ValueError('Unexpected number of exported accounts')

statements = ['START TRANSACTION;']
for row in rows:
    user, profile = row['users'], row['profiles']
    if user['id'] != profile['id'] or str(uuid.UUID(user['id'])) != user['id']:
        raise ValueError('Invalid account identifier')
    if user['role'] != 'user' or profile['role'] != 'user' or user['status'] != 'active':
        raise ValueError('Only active ordinary accounts may be imported')
    if not re.fullmatch(r'\$2[aby]\$\d\d\$[./A-Za-z0-9]{53}', user['password_hash']):
        raise ValueError('Unsupported password hash')
    for table, columns in COLUMNS.items():
        values = ', '.join(literal(row[table][key]) for key in columns)
        statements.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({values});")
statements.append('COMMIT;')
print('\n'.join(statements))
