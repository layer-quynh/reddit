from django.contrib.postgres.indexes import BTreeIndex
from django.db import models


class Post(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=False, blank=False)
    body = models.TextField()
    total_comments = models.IntegerField(default=0)

    class Meta:
        db_table = 'posts'
        BTreeIndex(
            'total_comments',
            name='total_comments_idx',
        )


class Comment(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False, null=False, blank=False)
    body = models.TextField()
    path = models.CharField(max_length=255, default='')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')

    class Meta:
        db_table = 'comments'
        BTreeIndex(
            ('post', 'created_at'),
            name='post_created_at_idx',
        )
        BTreeIndex(
            'path',
            name='path_idx'
        )
