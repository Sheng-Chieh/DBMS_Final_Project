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
        db_table = 'Application'
        managed = False # 關鍵！這行告訴 Django 不要管這張表，不要幫我 migrate！

    def __str__(self):
        return f"{self.student_name} 的申請單"

class CoffeeChatConfiguration(models.Model):
    alumni_name = models.CharField(max_length=50, verbose_name="發布校友")
    location_type = models.CharField(max_length=50, verbose_name="地點類型 (online/offline)")
    location_detail = models.CharField(max_length=255, verbose_name="地點詳細資訊")
    duration = models.IntegerField(verbose_name="時長(分鐘)")
    target_departments = models.CharField(max_length=100, default='無', verbose_name="目標科系")
    resume_match_rate = models.IntegerField(default=0, verbose_name="履歷契合度門檻")
    is_published = models.BooleanField(default=False, verbose_name="是否發布")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Configuration'
        managed = False  # 關鍵：告訴 Django 這張表我自己在 SQL 建好了

    def __str__(self):
        return f"{self.alumni_name} 的 Coffee Chat 設定"


class CoffeeChatTime(models.Model):
    coffee_chat = models.ForeignKey(CoffeeChatConfiguration, on_delete=models.CASCADE)
    
    chat_date = models.DateField(verbose_name="預約日期")
    start_time = models.TimeField(verbose_name="開始時間")
    end_time = models.TimeField(verbose_name="結束時間")

    class Meta:
        db_table = 'time'
        managed = False

    def __str__(self):
        return f"{self.chat_date} ({self.start_time} - {self.end_time})"