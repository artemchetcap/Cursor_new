from tortoise import fields, models

class User(models.Model):
    """
    Model representing a Telegram user.
    """
    id = fields.IntField(pk=True, description="Internal identifier")
    telegram_id = fields.BigIntField(unique=True, index=True, description="Unique ID in Telegram")
    username = fields.CharField(max_length=255, null=True, description="Username (@username)")
    full_name = fields.CharField(max_length=255, null=True, description="Full name")
    created_at = fields.DatetimeField(auto_now_add=True, description="Registration date")

    class Meta:
        table = "users"

    def __str__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})"


class SummaryRequest(models.Model):
    """
    Model representing a summary request (Analytics).
    """
    id = fields.IntField(pk=True, description="Unique request number")
    user = fields.ForeignKeyField("models.User", related_name="requests", description="Reference to user")
    content_type = fields.CharField(max_length=50, description="Content type (youtube, article, text, file)")
    source_url = fields.TextField(null=True, description="Source link (or null for text)")
    status = fields.CharField(max_length=50, default="processing", description="Result (success, error, processing)")
    tokens_used = fields.IntField(default=0, description="Number of tokens used (cost)")
    error_message = fields.TextField(null=True, description="Error text (if status is error)")
    created_at = fields.DatetimeField(auto_now_add=True, description="Request time")

    class Meta:
        table = "summary_requests"

    def __str__(self):
        return f"SummaryRequest(id={self.id}, user_id={self.user_id}, status={self.status})"

