from django.db import models

class User(models.Model):
    # 定义用户名和密码字段，最大长度分别为 50 和 100
    uid = models.CharField(max_length=50, unique=True)
    psw = models.CharField(max_length=100)

    def __str__(self):
        return self.uid