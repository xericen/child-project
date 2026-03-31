import peewee as pw

base = wiz.model("portal/season/orm").base("childcheck")

class Model(base):
    class Meta:
        db_table = 'photos'
        table_comment = '사진 정보'

    id              = pw.AutoField()
    category        = pw.CharField(max_length=20, null=False)
    server_id       = pw.IntegerField(null=False, default=0)
    target_user_id  = pw.IntegerField(null=False, default=0)
    title           = pw.CharField(max_length=200, null=True)
    meal_type       = pw.CharField(max_length=20, null=True)
    photo_date      = pw.DateField(null=True)
    photo_path      = pw.CharField(max_length=500, null=False)
    created_by      = pw.IntegerField(null=False)
    created_at      = pw.DateTimeField(constraints=[pw.SQL('DEFAULT CURRENT_TIMESTAMP')])
