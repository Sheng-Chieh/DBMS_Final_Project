from django.db import models

class CoffeeChatApplication(models.Model):
    # 確保名字是 student_name, alumni_name, scheduled_time
    student_name = models.CharField(max_length=50, verbose_name="申請學生")
    alumni_name = models.CharField(max_length=50, verbose_name="預約校友")
    scheduled_time = models.CharField(max_length=100, verbose_name="預約時段")

    experience_summary = models.TextField(verbose_name="自身經歷簡述")
    question_outline = models.TextField(verbose_name="具體提問大綱")

    status = models.CharField(max_length=20, default='pending', verbose_name="處理進度")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Application' # 指定資料表名稱改為 Application
        managed = False # 關鍵！這行告訴 Django 不要管這張表，不要幫我 migrate！

    def __str__(self):
        return f"{self.student_name} 的申請單"