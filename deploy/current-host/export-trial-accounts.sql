SELECT JSON_OBJECT(
  'users', JSON_OBJECT('id',u.id,'username',u.username,'email',u.email,
    'password_hash',u.password_hash,'role',u.role,'status',u.status,
    'last_login_at',u.last_login_at,'created_at',u.created_at,'updated_at',u.updated_at),
  'profiles', JSON_OBJECT('id',p.id,'username',p.username,'email',p.email,
    'role',p.role,'department_id',p.department_id,'phone',p.phone,'wechat',p.wechat,
    'avatar_url',p.avatar_url,'full_name',p.full_name,'gender',p.gender,
    'birth_date',p.birth_date,'bio',p.bio,'background_url',p.background_url,
    'selected_background',p.selected_background,'created_at',p.created_at,'updated_at',p.updated_at)
)
FROM users u JOIN profiles p ON p.id=u.id
WHERE u.role='user' AND p.role='user' AND u.status='active';
