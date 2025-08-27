from django.db import models

# Reports can be generated on the fly, so no need for a model unless storing generated reports
class Report(models.Model):
    report_type = models.CharField(max_length=20)  # daily, weekly, monthly
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()  # Store report data as JSON