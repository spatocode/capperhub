from django.db import models

class Comment(models.Model):
    text = models.TextField(max_length=1000)
    user = models.ForeignKey("core.UserAccount", on_delete=models.CASCADE, related_name="user_comments")
    post = models.ForeignKey("core.Comment", on_delete=models.CASCADE, related_name="comment_reply")
    wager = models.ForeignKey("core.SportsWager", on_delete=models.CASCADE, related_name="wager_comments", null=True)
    game = models.ForeignKey("core.Game", on_delete=models.CASCADE, related_name="game_comments", null=True)
    time_added = models.DateTimeField(auto_now_add=True)

class Like(models.Model):
    user = models.ForeignKey("core.UserAccount", on_delete=models.CASCADE, related_name="user_likes")
    comment = models.ForeignKey("core.Comment", on_delete=models.CASCADE, related_name="comment_likes")
